"""Numerical and boundary regressions for the real offline optics engine.

No browser, model, network or host edits. NODE_BIN may name a preinstalled Node>=18.
"""
import copy
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'plugins/offline-optics-lab/offline-optics-lab/engine'
NODE = os.environ.get('NODE_BIN') or shutil.which('node')
if not NODE:
    bundled = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    if bundled.is_file():
        NODE = str(bundled)


def obj(kind, ident, p1=None, p2=None, **kw):
    result = {'type': kind, 'id': ident, **kw}
    if p1 is not None:
        result['p1'] = dict(zip(('x', 'y'), p1))
        result['p2'] = dict(zip(('x', 'y'), p2))
    return result


def scene(*objects):
    return {'schema_version': 1, 'title': '数值验证', 'objects': list(objects)}


def ray(a=(100, 100), b=(200, 100), **kw):
    return obj('SingleRay', '光源', a, b, **kw)


def direction(segment):
    d = [segment['to'][k] - segment['from'][k] for k in ('x', 'y')]
    return [v / math.hypot(*d) for v in d]


@unittest.skipUnless(NODE, 'Node >=18 is required')
class OpticsEngineTest(unittest.TestCase):
    def run_scene(self, value, action='simulate'):
        p = subprocess.run([NODE, str(ENGINE / 'cli.mjs')], input=json.dumps({'scene': value, 'action': action}), text=True, capture_output=True, timeout=8, check=True)
        self.assertEqual(p.stderr, '')
        return json.loads(p.stdout)

    def ok(self, value):
        r = self.run_scene(value)
        self.assertTrue(r['ok'], r)
        self.assertEqual(r['version'], '1.0.0')
        return r

    def test_actual_detector_and_relative_power(self):
        r = self.ok(scene(ray(), obj('Detector', '探测器', (400, 20), (400, 200), bins=10)))
        d = r['detectors'][0]
        self.assertEqual(d['hits'], 1)
        self.assertAlmostEqual(d['power'], 1)
        self.assertAlmostEqual(sum(d['binData']), 1)
        self.assertEqual(len(r['segments']), 2)

    def test_mirror_reflection_angle(self):
        r = self.ok(scene(ray((100, 100), (200, 100 + 100 / math.sqrt(3))), obj('Mirror', '平面镜', (400, 0), (400, 600))))
        incoming, outgoing = map(direction, r['segments'])
        self.assertAlmostEqual(outgoing[0], -incoming[0], places=12)
        self.assertAlmostEqual(outgoing[1], incoming[1], places=12)

    def test_snell_and_fresnel_energy(self):
        r = self.ok(scene(ray((100, 100), (150, 100 + 50 * math.sqrt(3))), obj('PlaneGlass', '玻璃', (0, 300), (800, 300), refIndex=1.5)))
        escapes = [s for s in r['segments'] if s['type'] == 'escape']
        transmitted = next(s for s in escapes if direction(s)[1] > 0)
        self.assertAlmostEqual(direction(transmitted)[0], 1 / 3, places=12)
        self.assertAlmostEqual(sum(s['brightness'] for s in escapes), 1, places=12)
        expected_angle = math.degrees(math.asin(1 / 3))
        self.assertAlmostEqual(math.degrees(math.atan2(*direction(transmitted))), expected_angle, places=10)

    def test_total_internal_reflection(self):
        r = self.ok(scene(ray((200, 400), (200 + 100 * math.tan(math.radians(50)), 300)), obj('PlaneGlass', '玻璃', (0, 200), (900, 200), refIndex=1.5)))
        self.assertEqual(r['segments'][0]['interaction'], 'total_internal_reflection')
        self.assertEqual(len(r['segments']), 2)
        self.assertAlmostEqual(r['segments'][1]['brightness'], 1)
        a, b = map(direction, r['segments'])
        self.assertAlmostEqual(a[0], b[0])
        self.assertAlmostEqual(a[1], -b[1])

    def test_converging_and_diverging_lens(self):
        for focal, expected in ((100, 0), (-100, -100)):
            r = self.ok(scene(ray((0, -50), (100, -50)), obj('IdealLens', '透镜', (200, -150), (200, 150), focalLength=focal), obj('Detector', '屏幕', (300, -200), (300, 200))))
            hit = next(s for s in r['segments'] if s['object_id'] == '屏幕')
            self.assertAlmostEqual(hit['to']['y'], expected, places=10)

    def test_rotated_lens_is_compositional(self):
        base = scene(ray((0, -50), (100, -50)), obj('IdealLens', '透镜', (200, -150), (200, 150), focalLength=100), obj('Detector', '屏幕', (300, -200), (300, 200)))
        angle = .47
        for o in base['objects']:
            for k in ('p1', 'p2'):
                x, y = o[k]['x'], o[k]['y']
                o[k] = {'x': x*math.cos(angle)-y*math.sin(angle)+200, 'y': x*math.sin(angle)+y*math.cos(angle)+200}
        r = self.ok(base)
        hit = next(s for s in r['segments'] if s['object_id'] == '屏幕')['to']
        self.assertAlmostEqual(hit['x'], 300*math.cos(angle)+200, places=9)
        self.assertAlmostEqual(hit['y'], 300*math.sin(angle)+200, places=9)

    def test_slab_multiple_reflection_and_winding(self):
        glass = obj('Glass', '玻璃', path=[{'x':200,'y':0},{'x':300,'y':0},{'x':300,'y':200},{'x':200,'y':200}], refIndex=1.5)
        s = scene(ray(), glass, obj('Detector', '屏幕', (400, 0), (400, 200)))
        forward = self.ok(s)
        expected = (1 - .04) / (1 + .04)
        self.assertAlmostEqual(forward['detectors'][0]['power'], expected, delta=forward['stats']['lost_power'] + 1e-10)
        self.assertTrue(forward['stats']['truncated'])
        glass['path'].reverse()
        reverse = self.ok(s)
        self.assertEqual(forward['segments'], reverse['segments'])
        self.assertEqual(forward['detectors'], reverse['detectors'])

    def test_multielement_edit_changes_detector_distribution(self):
        examples = json.loads((ENGINE / 'examples.json').read_text())
        s = next(e['scene'] for e in examples if e['id'] == 'composed')
        before = self.ok(s)
        next(o for o in s['objects'] if o['type'] == 'IdealLens')['focalLength'] = 80
        after = self.ok(s)
        self.assertNotEqual(before['detectors'][0]['binData'], after['detectors'][0]['binData'])
        self.assertAlmostEqual(before['detectors'][0]['power'], after['detectors'][0]['power'])

    def test_beam_sampling_keeps_total_power(self):
        for count in (1, 9, 64):
            r = self.ok(scene(obj('Beam','光束',(100,20),(100,180),rayCount=count,brightness=2), obj('Detector','屏幕',(300,0),(300,200))))
            self.assertEqual(r['detectors'][0]['hits'], count)
            self.assertAlmostEqual(r['detectors'][0]['power'], 2)
            self.assertEqual(r['stats']['emitted_power'], 2)

    def test_detector_endpoints_and_one_sided(self):
        r = self.ok(scene(ray(), obj('Detector','屏幕',(400,0),(400,100),bins=10)))
        self.assertEqual(r['detectors'][0]['binData'][-1], 1)
        r = self.ok(scene(ray(), obj('Detector','屏幕',(400,200),(400,0),twoSided=False)))
        self.assertEqual(r['detectors'][0]['hits'], 0)

    def test_occluded_shared_vertex_does_not_fail_or_depend_on_order(self):
        far_a=obj('Mirror','远镜甲',(400,100),(400,200))
        far_b=obj('Mirror','远镜乙',(400,100),(500,100))
        close=obj('Mirror','近镜',(250,0),(250,200))
        results=[self.ok(scene(ray(), *items)) for items in ((far_a,far_b,close),(close,far_a,far_b),(far_b,close,far_a))]
        self.assertEqual(results[0]['segments'],results[1]['segments'])
        self.assertEqual(results[0]['segments'],results[2]['segments'])
        self.assertEqual(results[0]['segments'][0]['object_id'],'近镜')

    def test_shared_nearest_intersection_is_rejected(self):
        r=self.run_scene(scene(ray(),obj('Mirror','甲',(400,0),(400,200)),obj('Detector','乙',(400,0),(400,200))))
        self.assertFalse(r['ok']);self.assertEqual(r['error']['code'],'ambiguous_intersection')
        self.assertNotIn('segments',r)

    def test_source_on_boundary_is_rejected(self):
        r=self.run_scene(scene(ray(),obj('PlaneGlass','玻璃',(0,100),(800,100))))
        self.assertFalse(r['ok']);self.assertEqual(r['error']['code'],'source_on_surface')

    def test_mirror_cavity_is_bounded_and_discloses_lost_power(self):
        r=self.ok(scene(ray(),obj('Mirror','左',(0,0),(0,200)),obj('Mirror','右',(400,0),(400,200))))
        self.assertEqual(len(r['segments']),80)
        self.assertTrue(r['stats']['truncated']);self.assertEqual(r['stats']['lost_power'],1)
        self.assertTrue(any('截断' in w for w in r['warnings']))

    def test_invalid_scenes_do_not_bypass_whitelist(self):
        bad=[]
        s=scene(ray());s['backgroundImage']='https://invalid.example/a';bad.append((s,'unsupported_field'))
        s=scene(ray());s['objects'][0]['type']='CustomEquation';bad.append((s,'unsupported_type'))
        s=scene(ray());s['objects'][0]['p1']['x']=float('nan');bad.append((s,'invalid_json'))
        s=scene(ray());s['objects'][0]['brightness']=None;bad.append((s,'invalid_number'))
        for s,code in bad:
            result=self.run_scene(s)
            self.assertFalse(result['ok']);self.assertEqual(result['error']['code'],code)
        js="import {run} from './core.mjs'; console.log(JSON.stringify(run({scene:{schema_version:1,title:'测试',objects:[{id:'光源',type:'SingleRay',p1:{x:Infinity,y:0},p2:{x:10,y:0}}]}})))"
        p=subprocess.run([NODE,'--input-type=module','-e',js],cwd=ENGINE,text=True,capture_output=True,check=True)
        self.assertEqual(json.loads(p.stdout)['error']['code'],'invalid_number')

    def test_polygon_rejections(self):
        cases=[[(200,0),(300,200),(200,200),(300,0)],[(200,0),(250,0),(300,0),(300,200),(200,200)]]
        for path in cases:
            r=self.run_scene(scene(ray(),obj('Glass','玻璃',path=[dict(zip(('x','y'),p)) for p in path])))
            self.assertFalse(r['ok']);self.assertEqual(r['error']['code'],'invalid_polygon')
        g=obj('Glass','玻璃',path=[{'x':200,'y':0},{'x':300,'y':0},{'x':300,'y':200},{'x':200,'y':200}])
        h=copy.deepcopy(g);h['id']='重叠玻璃'
        r=self.run_scene(scene(ray(),g,h));self.assertEqual(r['error']['code'],'overlapping_glass')

    def test_cli_size_json_and_unsupported_action(self):
        for text,code in (('x','invalid_json'),(' '*131073,'input_too_large'),('{"action":"download","scene":{}}','invalid_action')):
            p=subprocess.run([NODE,str(ENGINE/'cli.mjs')],input=text,text=True,capture_output=True,check=True,timeout=8)
            self.assertEqual(json.loads(p.stdout)['error']['code'],code)

    def test_examples_and_validation_roundtrip(self):
        for example in json.loads((ENGINE/'examples.json').read_text()):
            r=self.ok(example['scene'])
            validated=self.run_scene(example['scene'],'validate')
            self.assertTrue(validated['ok']);self.assertEqual(r['scene'],validated['scene'])
            self.assertEqual(r,self.ok(validated['scene']))


if __name__=='__main__':
    unittest.main()
