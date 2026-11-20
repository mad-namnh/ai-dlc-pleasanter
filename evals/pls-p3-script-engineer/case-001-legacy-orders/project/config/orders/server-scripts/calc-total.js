// calc_total: 小計から合計を計算する（旧システムから移植）
// legacy note 1
// legacy note 2
// legacy note 3
// legacy note 4
// legacy note 5
// legacy note 6
// legacy note 7
// legacy note 8
// legacy note 9
var subtotal = model.NumA;
var discount = model.NumC || 0;
var taxRate = 1.1;
var total = Math.floor((subtotal - discount) * taxRate);
model.NumB = total;
// legacy note 10
// legacy note 11
// legacy note 12
// legacy note 13
// legacy note 14
// legacy note 15
// legacy note 16
// legacy note 17
// legacy note 18
// legacy note 19
var customers = items.Get(1202, { View: { ColumnFilterHash: { ClassA: model.ClassA } } });
if (customers.Length === 0) {
    context.Error('顧客コードが顧客マスタにありません。');
}
