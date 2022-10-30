
self.dataVar = [{isinCode:'KRS1'}, {isinCode:'KRS2'}, {isinCode:'KRS3'}, {isinCode:'KRS4'}, {isinCode:'KRS5'}];
// 최종적으로 보여주는 데이터를 담는 곳 

self.minutesAmountMap = new Map();
self.minutesPnlMap = new Map();


self.getAmountPerMinutes = function(isinCode, minutes){
  	return new Promise((resolve, reject) => {
  		resolve(isinCode + '_Amount_(' + minutes + ')');
    });
};
self.getPnlPerMinutes = function(isinCode, minutes){
  	return new Promise((resolve, reject) => {
  		resolve(isinCode + '_Pnl_(' + minutes + ')');
    });
};




self.getTradingCost = function(isinCode, minutes){
  
//  if (!self.minutesAmountMap.has(isinCode) || !self.minutesPnlMap.has(isinCode))
//    return 0;
  let key = isinCode + '_' + minutes
  let amountPerMinute = self.minutesAmountMap.get(key);
  let pnlPerMinute = self.minutesPnlMap.get(key);
  return amountPerMinute + pnlPerMinute;
};



self.updateTradingCost = function(itemList, minutesList){
  
  	// 정보를 얻는 부분
  	self.minutesAmountMap = new Map();
  	self.minutesPnlMap = new Map();
	let promises = [];
  
  
  	for (let minutes of minutesList){
          for (let item of itemList){
                let isinCode = item.isinCode;
                let key = isinCode + '_' + minutes;
                promises.push(
                  self.getAmountPerMinutes(isinCode, minutes).then((value) => {
                    self.minutesAmountMap.set(key, value);
                  })
                );
                promises.push(
                  self.getPnlPerMinutes(isinCode, minutes).then((value) =>{
                    self.minutesPnlMap.set(key, value);
                  })
                );
          }
    }
    
  	      	

  	// 정보를 다 가져와서 처리하는 부분
    Promise.all(promises).then(() => {
      	//viewData = [];
      	for (let minutes of minutesList){
            for (let item of itemList){
                item['costPer'+ minutes] = self.getTradingCost(item.isinCode, minutes);
                //viewData.push(item);
            }
        }
        console.log(itemList);
      	self.dataVar = itemList;//viewData;
	});
  
};






/// 자동 갱신시 실행해야되는 코드 
let refresh = function(){
	updateTradingCost(self.dataVar, [1, 5, 15]);
  	//console.log(self.dataVar);

  	//selt.ReactiveVar.set(self.dataVar);  // 여기서 최종적으로 업뎃된 데이터 테이블에 반영
}



refresh();
