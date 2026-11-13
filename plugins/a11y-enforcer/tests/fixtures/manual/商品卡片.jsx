export function 商品卡片({ 商品, 加入购物车 }) {
  return (
    <div className="card">
      <img src={商品.图片} />
      <h2>{商品.名称}</h2>
      <a onClick={() => 加入购物车(商品)}>加入购物车</a>
      <div onClick={() => 加入购物车(商品)} tabIndex={2}>快速购买</div>
      <button className="icon-button" onClick={() => 加入购物车(商品)}><HeartIcon /></button>
      <label htmlFor="数量">数量</label>
      <input id="数量" type="number" />
    </div>
  );
}
