"""生成原创合成WAV夹具；不读取用户曲库，不覆盖已有文件。"""
from pathlib import Path
import math
import struct
import wave

ROOT = Path(__file__).resolve().parents[2]


def prepare():
    base = ROOT/'dist/local-music-library/1.0.0'
    audio = base/'test-audio'; workspace = base/'manual-workspace'
    audio.mkdir(parents=True, exist_ok=True); workspace.mkdir(exist_ok=True)
    for name, hz in [('中文示例-低音.wav',220),('中文示例-高音.wav',440)]:
        path=audio/name
        if path.exists():
            continue
        with path.open('xb') as out:
            with wave.open(out,'wb') as f:
                f.setparams((1,2,16000,0,'NONE','not compressed'))
                f.writeframes(b''.join(struct.pack('<h',int(7000*math.sin(math.tau*hz*i/16000))) for i in range(16*16000)))
    bad=audio/'损坏音频.wav'
    if not bad.exists():bad.write_bytes(b'This is a deliberately invalid WAV fixture.\n')
    print('音频目录：',audio)
    print('独立工作目录：',workspace)


if __name__=='__main__':prepare()
