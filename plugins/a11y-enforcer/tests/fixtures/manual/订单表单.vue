<template>
  <div>
    <video autoplay src="promo.mp4"></video>
    <iframe src="https://example.com/map"></iframe>
    <select v-model="城市"><option>北京</option><option>上海</option></select>
    <textarea v-model="备注"></textarea>
    <span @click="提交">提交订单</span>
    <button accesskey="s" aria-label="保存订单">保存</button>
  </div>
</template>
<style>
button { outline: none; }
</style>
