// 値引が小計を超えないこと
if (model.NumC > model.NumA) {
    context.Error('値引は小計以下にしてください。');
}
