self.dataVar = [{isinCode:'KRS1'}, {isinCode:'KRS2'}, {isinCode:'KRS3'}, {isinCode:'KRS4'}, {isinCode:'KRS5'}];
// 최종적으로 보여주는 데이터를 담는 곳 

self.getAmountPerMinutes = function(isinCode, minutes){
  	return new Promise((resolve, reject) => {
  		resolve(isinCode + '_Amount_' + minutes);
    });
};
self.getPnlPerMinutes = function(isinCode, minutes){
  	return new Promise((resolve, reject) => {
  		resolve(isinCode + '_Pnl_' + minutes);
    });
};




self.getTradingCost = function(isinCode, minutes){
        	
  let tradingCost;
  let promises = [];
  let resultMap = new Map();
  
  promises.push(
    self.getAmountPerMinutes(isinCode, minutes).then((value) => {
      resultMap.set('amount', value);
      //resultMap.set('amount' value['Amount'])
    })
  );
  promises.push(
    self.getPnlPerMinutes(isinCode, minutes).then((value) =>{
      resultMap.set('tRealized', value);
      //resultMap.set('amount' value['tRealized'])
    })
  );
  Promise.all(promises).then(() => {
        if (resultMap.has('amount') && resultMap.has('tRealized')){
          	let minutesAmount = resultMap.get('amount');
  			let minutesPnl = resultMap.get('tRealized');
          	tradingCost = minutesAmount + minutesPnl;
          	console.log(traingCost);
        }
    	else
    		tradingCost = 0;
  });
  console.log(tradingCost);
  return tradingCost;
};



self.updateTradingCost = function(itemList, minutes){
  
  	viewData = []; 
    for (item of itemList){
        item['costPer'+ minutes] = self.getTradingCost(item.isinCode, minutes);
      	viewData.push(item);
    }
  
	self.dataVar = viewData; 
};






/// 자동 갱신시 실행해야되는 코드 
let refresh = function(){
	updateTradingCost(self.dataVar, 1);
  	updateTradingCost(self.dataVar, 5);
	updateTradingCost(self.dataVar, 15);
  	//self.ReactiveVar.set(self.dataVar);  // 여기서 최종적으로 업뎃된 데이터 테이블에 반영
  	console.log(self.dataVar);
}



refresh();
