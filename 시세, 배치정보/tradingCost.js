import {ReactiveVar} from 'meteor/reactive-var';
import {flux} from "@influxdata/influxdb-client";

require('../../lib/util.js');

class BidAskAmount {
    isinCode;
    bidAmount;
    askAmount;

    constructor(isinCode, bidAmount = 0, askAmount = 0) {
        this.isinCode = isinCode;
        this.bidAmount = bidAmount;
        this.askAmount = askAmount;
    }

    update(bidAmount, askAmount) {
        this.bidAmount += bidAmount;
        this.askAmount += askAmount;
    }
}

Template.TradingLimitViewerTmpl.onCreated(function () {
    let self = this;
    FEPClientCenter.init();
    LiveSiseClient.init();
    LiveSiseClient.subscribe('BidAsk', "KRD020020016", "tradingLimitViewer", function (t) {
        let baObj = JSON.parse(t);
        self.indexPrice = Number(baObj.mid) / 100;
        document.getElementById("indexPrice").innerText = Number(self.indexPrice).toFixed(2);
        self.updateTimeLabel("indexPriceLastUpdated");

        if (self.indexPriceForGreeks == null)
            self.indexPriceForGreeks = self.indexPrice;
    });

    self.dataOption = new ReactiveVar(null);
    self.dataVar = new ReactiveVar([]);
    self.optionBidAskAmountMap = new Map();

    self.basketDataOption = new ReactiveVar(null);
    self.basketDataVar = new ReactiveVar([]);

    self.tableOption = new ReactiveVar(null);
    self.tableVar = new ReactiveVar([]);
    self.graphVar = new ReactiveVar([]);

    self.refresh = true;
    self.updateTimerId = null;

    self.minutesTRealizedMap = new Map();
    self.minutesTEvalMap = new Map();
    self.minutesAmountMap = new Map();

    self.optionBookCode = "S:KOSPI_OPT";
    self.basketBookCode = "M:KRD020020016";

    self.bookdb = Meteor.subscribe("bookItemLive");
    self.basketdb = Meteor.subscribe("basketElement", self.basketBookCode);

    self.pnlMap = new Map();
    self.deltaMap = new Map();

    self.minutesList = [5, 15, 30];

    self.getAmountPerMinutes = function (isinCode, minutes) {
        let startLast = (-minutes).toString() + 'm'
        let stopLast = 'now()';
        let fluxQuery = "from(bucket: \"MM\")\n";
        fluxQuery = influxDBMaster.addRangeQuery(fluxQuery, startLast, stopLast);
        fluxQuery = influxDBMaster.addFilterQuery(fluxQuery, {"_measurement": 'fepTradeLog'});
        fluxQuery = influxDBMaster.addFilterQuery(fluxQuery, {"_field": 'amount'});
        fluxQuery = influxDBMaster.addFilterQuery(fluxQuery, {"bookCode": self.optionBookCode, "isinCode": isinCode});
        fluxQuery = influxDBMaster.addAggregateWindowQuery(fluxQuery, '24h', 'sum', false);
        return influxDBMaster.getFromDB(fluxQuery);
    };

    self.getPnlPerMinutes = function (isinCode, minutes) {
        let startLast = (-(minutes + 5)).toString() + 'm'
        let stopLast = (-minutes).toString() + 'm';
        let fluxQuery = "from(bucket: \"BookPnL\")\n";
        fluxQuery = influxDBMaster.addRangeQuery(fluxQuery, startLast, stopLast);
        fluxQuery = influxDBMaster.addFilterQuery(fluxQuery, {"_measurement": 'bookItemLive'});
        fluxQuery = influxDBMaster.addFilterQuery(fluxQuery, {"_field": ['tEval', 'tRealized']});
        fluxQuery = influxDBMaster.addFilterQuery(fluxQuery, {"bookCode": self.optionBookCode, "isinCode": isinCode});
        fluxQuery = influxDBMaster.addAggregateWindowQuery(fluxQuery, '24h', 'last', false);
        return influxDBMaster.getFromDB(fluxQuery);
    };

    self.getJoinString = function (str1, str2) {
        return str1 + '_' + str2;
    };

    self.getTradingCost = function (isinCode, minutes) {
        let key = self.getJoinString(isinCode, minutes);

        let delta = self.deltaMap.get(isinCode);
        let amount = self.minutesAmountMap.get(key);
        let minutesAmount = amount * delta;

        let totalPnl = self.pnlMap.get(isinCode);
        let tRealized = self.minutesTRealizedMap.get(key);
        let tEval = self.minutesTEvalMap.get(key);
        let minutesPnl = totalPnl - (tRealized + tEval);
        let tradingCost = minutesPnl / minutesAmount

        if (isNaN(tradingCost) || !isFinite(tradingCost))
            return 0;
        return tradingCost;
    };

    self.updateTradingCost = function () {
        let promises = [];
        let itemList = self.dataVar.get();
        for (let minutes of self.minutesList) {
            for (let item of itemList) {
                let isinCode = item.isinCode;
                let key = self.getJoinString(isinCode, minutes);
                promises.push(
                    self.getAmountPerMinutes(isinCode, minutes).then((value) => {
                        self.minutesAmountMap.set(key, value['amount']);
                    })
                );
                promises.push(
                    self.getPnlPerMinutes(isinCode, minutes).then((value) => {
                        self.minutesTEvalMap.set(key, value['tEval']);
                        self.minutesTRealizedMap.set(key, value['tRealized']);
                    })
                );
            }
        }
        Promise.all(promises).then(() => {
            for (let minutes of self.minutesList)
                for (let item of itemList){
                    let toColumn = self.getJoinString('costPer', minutes);
                    item[toColumn] = self.getTradingCost(item.isinCode, minutes);
                }
            self.dataVar.set(itemList);
        });
    };

    self.updatePnl = function () {
        let data = BookBalance.find({bookCode: self.optionBookCode}).fetch();
        if (data.length === 0) {
            console.log("북 손익 데이터가 없습니다.");
            return;
        }

        for (const pnl of data) {
            let isinCode = pnl.isinCode;
            // 현재 포지션에 대한 손익을 같이 보기 위해 평가 + 실현 손익으로 계산한다
            let tPnl = pnl.tRealized + pnl.tEval;
            self.pnlMap.set(isinCode, tPnl);
        }
    };

    self.updateBasket = function () {
        let data = BasketElement.find({bookCode: self.basketBookCode}).fetch();
        if (data.length === 0) {
            console.log("바스켓 데이터가 없습니다.");
            return;
        }

        let result = [];
        for (const basketElement of data) {
            let isinCode = basketElement.isinCode;
            let korean = basketElement.korean;
            let shortLimit = basketElement.futAmtToTrade;
            let longLimit = basketElement.longFutAmtToTrade;
            let remainAmount = basketElement.unSubmitted;

            result.push({
                isinCode, korean, shortLimit, longLimit, remainAmount
            });
        }

        self.basketDataVar.set(result);
    }

    self.updateAllData = function () {
        for (const client of FEPClientCenter.getAllFEPClient())
            client.todayTotalQuantityRequest();
        self.updateGreeks();
    }

    self.autoRefresh = function (interval) {
        self.updateTimerId = setTimeout(function () {
            self.updateAllData();

            if (self.refresh)
                self.autoRefresh(interval);
        }, interval);
    }

    self.startAutoRefresh = function (interval) {
        // self.updateAllData();
        self.autoRefresh(interval);
    }

    self.getTimeIntegerForQuery = function () {
        let date = new Date();
        let hour = date.getHours();
        let minutes = date.getMinutes();
        if (minutes === 0) {
            hour -= 1;
            minutes = 59;
        }

        let timeInteger = hour * 1_00_00_00 + minutes * 1_00_00;
        if (timeInteger >= 15_45_00_00)
            timeInteger = 15_45_00_00;
        return timeInteger;
    }

    self.queryDate = Number(Util.getDateString(new Date(), ''));
    self.queryTime = self.getTimeIntegerForQuery();

    self.greeksdb = Meteor.subscribe("marketGreeks", self.queryDate, self.queryTime);
    self.greeksMap = new Map();

    self.expiredMode = false;
    self.indexPrice = null;

    self.updateIndexPriceWithClosingPrice = function (closingPrice, isToday) {
        self.indexPrice = closingPrice;
        document.getElementById("indexPrice").innerText = Number(closingPrice).toFixed(2);
        document.getElementById("indexPriceLastUpdated").innerText = isToday ? "종가" : "전일 종가";

        if (self.indexPriceForGreeks == null)
            self.indexPriceForGreeks = closingPrice;
    };

    if (self.queryTime <= 9_00_00_00) {
        let yesterday = new Date(new Date().getTime() - 24 * 60 * 60 * 1000);
        let queryDate = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate());
        self.closingpricedb = Meteor.subscribe("closingPriceIndex", queryDate);
        this.autorun(() => {
            if (self.closingpricedb.ready()) {
                let doc = ClosingPriceIndex.findOne({indexIsin: "KRD020020016"});
                if (doc === null || doc === undefined) {
                    console.log("K200 종가를 찾을 수 없었습니다.");
                    return;
                }
                console.log(doc);

                let price = Number(doc.price) / 100;
                self.updateIndexPriceWithClosingPrice(price, false);
            }
        });
    } else if (self.queryTime >= 15_30_00_00) {
        let today = new Date();
        let queryDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        self.closingpricedb = Meteor.subscribe("closingPriceIndex", queryDate);
        this.autorun(() => {
            if (self.closingpricedb.ready()) {
                let doc = ClosingPriceIndex.findOne({indexIsin: "KRD020020016"});
                if (doc === null || doc === undefined) {
                    console.log("K200 종가를 찾을 수 없었습니다.");
                    return;
                }
                console.log(doc);

                let price = Number(doc.price) / 100;
                self.updateIndexPriceWithClosingPrice(price, true);

                document.getElementById("autoRefresh").checked = false;
                self.refresh = false;
            }
        });
    }

    // Greeks 입수 시점의 지수를 알고 있어야 델타를 비교적 정확하게 계산할 수 있는데, 현재는 최대 1분 전의 Greeks을 가져오므로, 델타 계산이 정확하지 않다.
    // 일단은 DB에서 Greeks을 가져올 때의 지수값을 Greeks 입수 시점의 지수값이라고 하자.
    self.indexPriceForGreeks = null;

    // self.queryTime (hhmmssxx) -> "hh:mm:ss"
    self.getTimeStringFromTimeInteger = function (time) {
        if (time === null || time === undefined)
            time = self.queryTime;

        let leftPad = function (val) {
            return val >= 10 ? val : `0${val}`;
        };

        let hour = leftPad(~~(time / 1_00_00_00));
        time %= 1_00_00_00;
        let min = leftPad(~~(time / 1_00_00));
        time %= 1_00_00;
        let sec = leftPad(~~(time / 1_00));
        let ms = time % 1_00;

        return [hour, min, sec].join(":");
    }

    self.updateGreeks = function () {
        self.updatePnl();
        self.updateBasket();
        self.updateTradingCost();

        let nextQueryTime = self.getTimeIntegerForQuery();
        if (self.queryTime === nextQueryTime) {
            console.log("no update greeks");
            return;
        }

        self.queryTime = nextQueryTime;
        self.greeksdb = Meteor.subscribe("marketGreeks", self.queryDate, self.queryTime);
        if (self.indexPrice != null) {
            self.indexPriceForGreeks = self.indexPrice;
            console.log("IndexPriceForGreeks Updated (" + Util.getTimeString(new Date()) + ") : " + self.indexPriceForGreeks + " (" + self.queryTime + ")");
        }
    };

    self.updateTimeLabel = function (elementId) {
        document.getElementById(elementId).innerText = Util.getTimeString(new Date());
    }

    for (const client of FEPClientCenter.getAllFEPClient()) {
        client.init();
        client.registerHandler("todayTotalQuantityData", "FEPServerResponse", this, async function (obj, template, client) {
            if (obj.trCode !== "FEPServerResponse") {
                console.log("FEPServerResponse가 요청하지 않은 응답은 무시합니다.");
                console.log(obj);
                return;
            }

            let serverId = client.getServerId();
            let amountMap = new Map();

            for (const info of obj.totalQuantityList) {
                let isinCode = info.isinCode;
                if (!isinCode.startsWith("KR4205") && !isinCode.startsWith("KR4305"))
                    continue;

                let bidAskAmount;
                if (amountMap.has(isinCode)) {
                    bidAskAmount = amountMap.get(isinCode);
                } else {
                    bidAskAmount = new BidAskAmount(isinCode);
                    amountMap.set(isinCode, bidAskAmount);
                }

                bidAskAmount.update(info.bidQuantity, info.askQuantity);
            }

            for (const [code, bidAskAmount] of amountMap) {
                let idAmountMap = null;
                if (!self.optionBidAskAmountMap.has(code)) {
                    idAmountMap = new Map();
                    self.optionBidAskAmountMap.set(code, idAmountMap);
                } else {
                    idAmountMap = self.optionBidAskAmountMap.get(code);
                }

                idAmountMap.set(serverId, bidAskAmount);
            }

            self.updateTimeLabel("contractLastUpdated");
            self.updateDataVar();
            self.updateGraph();
        });
    }

    self.getClosestStrikePrice = function (price) {
        let candidateLowPrice = ~~(price / 2.5) * 2.5;
        let candidateHighPrice = candidateLowPrice + 2.5;

        if (Math.abs(candidateLowPrice - price) <= Math.abs(candidateHighPrice - price))
            return candidateLowPrice;
        else
            return candidateHighPrice;
    };

    self.calculateDelta = function (code, strikePrice, price = null) {
        if (price === null)
            price = self.indexPrice;

        if (self.expiredMode) {
            let callPut = code.startsWith("KR42") ? "C" : "P";
            if (callPut === "C")
                return strikePrice < price ? 1 : 0;
            else
                return strikePrice > price ? -1 : 0;
        } else {
            let greeks = self.greeksMap.get(code);
            if (greeks === null || greeks === undefined)
                return 0;

            // Greeks 입수 시점의 가격이 없거나 기준 가격이 지수값일 경우에는 Greeks Delta를 그대로 사용한다.
            if (self.indexPriceForGreeks === null || price === self.indexPrice)
                return greeks.Delta;

            let estimatedDelta = greeks.Delta + greeks.Gamma * (price - self.indexPriceForGreeks);
            if (estimatedDelta > 1)
                estimatedDelta = 1;
            else if (estimatedDelta < -1)
                estimatedDelta = -1;

            return estimatedDelta;
        }
    }

    self.updateGraph = function () {
        if (self.indexPrice == null)
            return;

        let closestStrikePrice = self.getClosestStrikePrice(self.indexPrice);

        let priceList = [];
        for (let i = -4; i <= 4; i++) {
            let strikePrice = closestStrikePrice + 2.5 * i;
            priceList.push(strikePrice - 0.01, strikePrice, strikePrice + 0.01);
        }

        let dataList = self.dataVar.get();
        if (dataList === null || dataList === undefined) {
            console.log("no contract data");
            return;
        }

        let graphData = [];
        for (const price of priceList) {
            let limit = 0;
            for (const data of dataList) {
                let isinCode = data.isinCode;
                let callPut = data.callPut;
                let amount = 0;
                if (callPut === "C")
                    amount = data.bidAmount;
                else if (callPut === "P")
                    amount = data.askAmount;

                let delta = self.calculateDelta(data.isinCode, data.strikePrice, price);
                limit += Math.abs(delta) * amount;
            }

            limit = ~~(limit);
            graphData.push({price, limit});
        }

        let table = [];
        for (const point of graphData) {
            let price = point.price;
            let limit = point.limit;

            if (self.expiredMode) {
                if (price % 2.5 !== 0)
                    table.push(point);
            } else {
                if (price % 2.5 === 0)
                    table.push(point);
            }
        }

        self.graphVar.set(graphData);
        self.tableVar.set(table);
    };

    self.updateDataVar = function () {
        let list = [];
        let totalAmountMap = new Map();

        for (const [code, idAmountMap] of self.optionBidAskAmountMap) {
            let bidAmount = 0;
            let askAmount = 0;

            for (const [id, bidAskAmount] of idAmountMap) {
                bidAmount += bidAskAmount.bidAmount;
                askAmount += bidAskAmount.askAmount;
            }

            let totalAmount = new BidAskAmount(code, bidAmount, askAmount);

            totalAmountMap.set(code, totalAmount);
        }

        for (const [code, bidAskAmount] of totalAmountMap) {
            let bidAmount = bidAskAmount.bidAmount;
            let askAmount = bidAskAmount.askAmount;

            let callPut = code.startsWith("KR42") ? "C" : "P";

            let info = ItemMaster.getFuturesItemInfo(code);
            let strikePrice = 0;
            if (info != null)
                strikePrice = info.strikePrice;
            let moneyType = "UNKNOWN";
            if (info.ATM구분 === 1)
                moneyType = "ATM";
            else if (info.ATM구분 === 2)
                moneyType = "ITM";
            else if (info.ATM구분 === 3)
                moneyType = "OTM";

            let delta = self.calculateDelta(code, strikePrice);
            self.deltaMap.set(code, delta);

            let oppositeCode = IsinCodeUtil.getOppositeK200MiniOptionCode(code);
            let oppositeBidAmount, oppositeAskAmount;
            oppositeBidAmount = oppositeAskAmount = 0;
            if (oppositeCode === code) {
                oppositeCode = "";
            } else {
                if (totalAmountMap.has(oppositeCode)) {
                    let oppositeBidAskAmount = totalAmountMap.get(oppositeCode);
                    oppositeBidAmount = oppositeBidAskAmount.bidAmount;
                    oppositeAskAmount = oppositeBidAskAmount.askAmount;
                }
            }

            let futuresCount = 0;
            if (callPut === "C")
                futuresCount = delta * bidAmount;
            else if (callPut === "P")
                futuresCount = -delta * askAmount;

            let pnl = 0;
            if (self.pnlMap.has(code))
                pnl = self.pnlMap.get(code);

            let cost = 0;
            if (futuresCount !== 0)
                cost = pnl / futuresCount;


            let data = {
                isinCode: code,
                callPut: callPut,
                moneyType: moneyType,
                totalAmount: bidAmount + askAmount,
                bidAmount: bidAmount,
                askAmount: askAmount,
                futuresCount: futuresCount,
                delta: delta,
                strikePrice: strikePrice,
                oppositeIsinCode: oppositeCode,
                oppositeAskAmount: oppositeAskAmount,
                oppositeBidAmount: oppositeBidAmount,
                pnl: pnl,
                totalCost: cost,
            }

            for (let minutes of self.minutesList){
                let toColumn = self.getJoinString('costPer', minutes);
                data[toColumn] = self.getTradingCost(code, minutes);
            }

            list.push(data);
        }
        self.dataVar.set(list);
    };

    self.clearTable = function () {
        self.dataVar.set([]);
    };
});

Template.TradingLimitViewerTmpl.onRendered(function () {
    let self = Template.instance();
    self.updateGreeks();

    this.autorun(() => {
        if (self.greeksdb.ready()) {
            let greeksList = MarketGreeks.find({}).fetch();
            for (const greeksDoc of greeksList)
                self.greeksMap.set(greeksDoc.isinCode, greeksDoc);

            document.getElementById("optionDeltaLastUpdated").innerText = self.getTimeStringFromTimeInteger();
        }
    });

    this.autorun(() => {
        if (Util.isItemMasterReady()) {
            for (const client of FEPClientCenter.getAllFEPClient())
                client.todayTotalQuantityRequest();

            self.startAutoRefresh(10_000);
        }
    });
});

Template.TradingLimitViewerTmpl.onDestroyed(function () {
    for (const client of FEPClientCenter.getAllFEPClient())
        client.unregisterHandler("todayTotalQuantityData", "FEPServerResponse");

    LiveSiseClient.unsubscribe('BidAsk', "KRD020020016", "tradingLimitViewer");
});

Template.TradingLimitViewerTmpl.helpers({

    tradingLimitData: function () {
        let self = Template.instance();
        let arr = self.dataVar.get();
        self.dataOption.set({dataArray: arr});
        return self.dataOption;
    },

    tradingLimitOptions: function () {
        let self = Template.instance();
        let height = self.tableHeight > 0 ? self.tableHeight : 520;
        let option = {
            columnHeaderVertAlign: "bottom",
            height: height, // set height of table (in CSS or here), this enables the Virtual DOM and improves render speed dramatically (can be any valid css height value)
            layout: "fitDataFill", //fit columns to width of table (optional)
            columns: [ //Define Table Columns
                {
                    field: "issueName", title: "종목명", visible: true, width: 160, download: true,
                    mutator: function (value, data, type, params, component) {
                        let obj = ItemMaster.getProductName(data.isinCode);
                        if (obj == null)
                            return "";
                        return obj;
                    },
                    sorter: Util.stringComparatorForTabulator,
                },
                {field: "isinCode", title: "isinCode", visible: false, width: 100, download: true},
                {
                    field: "strikePrice", title: "행사가", visible: true, sorter: "number", width: 65, download: true,
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.formatNumber(data, true, true, 1, false);
                    },
                },
                {
                    field: "delta", title: "Delta", visible: true, download: true,
                    sorter: "number", width: 60,
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.formatNumber(data, true, true, 3, false);
                    },
                },
                {
                    field: "futuresCount", title: "선물 환산", visible: true, download: true,
                    sorter: "number", width: 80,
                    // mutator: function (value, data, type, params, component) {
                    //     let callPut = data.callPut;
                    //     if (callPut === "C")
                    //         return data.delta * data.bidAmount;
                    //     else if (callPut === "P")
                    //         return -data.delta * data.askAmount;
                    //
                    //     return 0;
                    // },
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.formatNumber(data, true, true, 0, false);
                    },
                    bottomCalc: "sum",
                    bottomCalcFormatter: function (cell, formatterParams) {
                        return Util.formatNumber(cell.getValue(), true, true, 0, false);
                    },
                },
                {
                    title: "거래량",
                    columns: [
                        {
                            field: "totalAmount", title: "Total", visible: true, download: true, sorter: "number",
                            width: 60,
                            formatter: function (cell, formatterParams) {
                                let data = cell.getValue();
                                return Util.formatNumber(data, true, true, 0, false);
                            },
                        },
                        {
                            field: "bidAmount", title: "Bid", visible: true, download: true, sorter: "number",
                            width: 60,
                            formatter: function (cell, formatterParams) {
                                let data = cell.getValue();
                                return Util.formatNumber(data, true, true, 0, false);
                            },
                        },
                        {
                            field: "askAmount", title: "Ask", visible: true, download: true, sorter: "number",
                            width: 60,
                            formatter: function (cell, formatterParams) {
                                let data = cell.getValue();
                                return Util.formatNumber(data, true, true, 0, false);
                            },
                        },
                    ],
                },
                {
                    title: "반대편",
                    columns: [
                        {
                            field: "oppositeIsinCode",
                            title: "oppositeIsinCode",
                            visible: false,
                            width: 100,
                            download: true
                        },
                        {
                            field: "oppositeIssueName", title: "종목", visible: true, width: 160, download: true,
                            mutator: function (value, data, type, params, component) {
                                let obj = ItemMaster.getProductName(data.oppositeIsinCode);
                                if (obj == null)
                                    return "";
                                return obj;
                            },
                            sorter: Util.stringComparatorForTabulator,
                        },
                        {
                            field: "oppositeAmount", title: "거래량", visible: true, download: true,
                            sorter: "number", width: 70,
                            mutator: function (value, data, type, params, component) {
                                if (data.callPut === "C")
                                    return data.oppositeAskAmount;
                                else if (data.callPut === "P")
                                    return data.oppositeBidAmount;

                                return 0;
                            },
                            formatter: function (cell, formatterParams) {
                                let data = cell.getValue();
                                return Util.formatNumber(data, true, true, 0, false);
                            },
                        }
                    ]
                },
                {
                    field: "callPutBalance", title: "Balance", visible: true, download: true, sorter: "number",
                    width: 75,
                    mutator: function (value, data, type, params, component) {
                        if (data.callPut === "C")
                            return data.oppositeAskAmount - data.bidAmount;
                        else if (data.callPut === "P")
                            return data.oppositeBidAmount - data.askAmount;

                        return 0;
                    },
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.addUpDownColor(Util.formatNumber(data, true, true, 0, false), data, 0);
                    },
                },
                {
                    field: "pnl", title: "북 손익", visible: true, download: true, sorter: "number",
                    width: 85,
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.addUpDownColor(Util.formatNumber(data, true, true, 0, false), data, 0);
                    },
                    bottomCalc: "sum",
                    bottomCalcFormatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.addUpDownColor(Util.formatNumber(data, true, true, 0, false), data, 0);
                    },
                },
            ],
            rowFormatter: function (row) {
                let data = row.getData();
                if (data.moneyType === "ITM") {
                    row.getElement().style.backgroundColor = "rgba(255,187,187,0.3)";
                } else if (data.moneyType === "ATM") {
                    row.getElement().style.backgroundColor = "rgba(187,187,255,0.3)";
                } else {
                    row.getElement().style.backgroundColor = "";
                }
            },
            keybindings: {"copyToClipboard": false,},
            initialSort: [
                {column: "issueName", dir: "asc"},
            ],
            clipboard: true,
        };
        let toColumns = [
            {
                field: "totalCost", title: "전체", visible: true, download: true, sorter: "number",
                width: 70,
                formatter: function (cell, formatterParams) {
                    let data = cell.getValue();
                    return Util.addUpDownColor(Util.formatNumber(data, true, true, 0, false), data, 0);
                },
            },
        ];
        for (const minutes of self.minutesList)
            toColumns.push(
                {
                    field: self.getJoinString('costPer', minutes), title: minutes + "분", visible: true, download: true, sorter: "number",
                    width: 70,
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.addUpDownColor(Util.formatNumber(data, true, true, 0, false), data, 0);
                    },
                }
            )
        option.columns.push({
            title: "TO 비용",
            columns: toColumns,
        })
        return option;
    },

    isDBReady: function () {
        let self = Template.instance();
        return Util.isItemMasterReady() && self.bookdb.ready() && self.basketdb.ready();
    },

    payoffTmplData: function () {
        let template = Template.instance();
        return {
            defaultRange: 1000,
            dataVar: template.graphVar,
            width: 600,
            xLabel: "price",
            yLabelList: ["limit"],
            circleYLabelList: ["limit"]
        };
    },

    graphData: function () {
        let self = Template.instance();
        let arr = self.tableVar.get();
        self.tableOption.set({dataArray: arr});
        return self.tableOption;
    },

    graphDataOptions: function () {
        let self = Template.instance();
        let height = self.tableHeight > 0 ? self.tableHeight : 350;
        let option = {
            columnHeaderVertAlign: "bottom",
            height: height, // set height of table (in CSS or here), this enables the Virtual DOM and improves render speed dramatically (can be any valid css height value)
            layout: "fitDataFill", //fit columns to width of table (optional)
            columns: [ //Define Table Columns
                {
                    field: "price", title: "지수", visible: true, sorter: "number", width: 55, download: true,
                    formatter: function (cell, formatterParams) {
                        let price = cell.getValue();
                        let floatPadLen = self.expiredMode ? 2 : 1;
                        let numberFormattingResult = Util.formatNumber(price, true, true, floatPadLen, false);

                        if (self.indexPrice == null)
                            return numberFormattingResult;

                        if (self.indexPrice <= price)
                            return Util.addColor(numberFormattingResult, "red");
                        else
                            return Util.addColor(numberFormattingResult, "blue");
                    },
                },
                {
                    field: "limit", title: "limit", visible: true, sorter: "number", width: 65, download: true,
                    formatter: function (cell, formatterParams) {
                        let limit = cell.getValue();
                        let numberFormattingResult = Util.formatNumber(limit, true, true, 0, false);

                        let row = cell.getRow();
                        if (row === null || row === undefined)
                            return numberFormattingResult;

                        let rowData = row.getData();
                        if (rowData === null || row === undefined)
                            return numberFormattingResult;

                        let price = rowData.price;
                        if (price === null || price === undefined)
                            return numberFormattingResult;

                        if (self.indexPrice == null)
                            return numberFormattingResult;

                        if (self.indexPrice * 0.99 <= price && price <= self.indexPrice * 1.01)
                            return Util.addColor(numberFormattingResult, "#FF0000", "bold");
                        else if (self.indexPrice * 0.98 <= price && price <= self.indexPrice * 1.02)
                            return Util.addColor(numberFormattingResult, "#FF8E00", "bold");
                        else if (self.indexPrice * 0.97 <= price && price <= self.indexPrice * 1.03)
                            return Util.addColor(numberFormattingResult, "#7CCF19", "bold");

                        return numberFormattingResult;
                    },
                },
            ],
            keybindings: {"copyToClipboard": false,},
            initialSort: [
                {column: "price", dir: "desc"},
            ],
            clipboard: true,
        };

        return option;
    },

    basketData: function () {
        let self = Template.instance();
        let arr = self.basketDataVar.get();
        self.basketDataOption.set({dataArray: arr});
        return self.basketDataOption;
    },

    basketDataOptions: function () {
        let self = Template.instance();
        let height = self.tableHeight > 0 ? self.tableHeight : 350;
        let option = {
            columnHeaderVertAlign: "bottom",
            height: height, // set height of table (in CSS or here), this enables the Virtual DOM and improves render speed dramatically (can be any valid css height value)
            layout: "fitDataFill", //fit columns to width of table (optional)
            columns: [ //Define Table Columns
                {field: "isinCode", title: "isinCode", visible: false, width: 100, download: true},
                {field: "korean", title: "종목명", visible: true, width: 125, download: true},
                {
                    title: "매도", field: "shortLimit", sorter: "number", hozAlign: "right", width: 60,
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.addUpDownColor(Util.formatNumber(data, true, true, 0, false), data, 0);
                    },
                    bottomCalc: "max",
                    bottomCalcFormatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.addUpDownColor(Util.formatNumber(data, true, true, 0, false), data, 0);
                    }
                },
                {
                    title: "매수", field: "longLimit", sorter: "number", hozAlign: "right", width: 60,
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.addUpDownColor(Util.formatNumber(data, true, true, 0, false), data, 0);
                    },
                    bottomCalc: "min",
                    bottomCalcFormatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.addUpDownColor(Util.formatNumber(data, true, true, 0, false), data, 0);
                    }
                }
            ],
            rowFormatter: function (row) {
                let data = row.getData();
                if (data.hasOwnProperty("remainAmount")) {
                    if (data.remainAmount > 0) { // 매수잔량 있음
                        row.getElement().style.backgroundColor = "rgba(255,187,187,0.3)";
                    } else if (data.remainAmount < 0) { // 매도잔량 있음
                        row.getElement().style.backgroundColor = "rgba(187,187,255,0.3)";
                    } else {
                        row.getElement().style.backgroundColor = "";
                    }
                } else {
                    row.getElement().style.backgroundColor = "";
                }
            },
            keybindings: {"copyToClipboard": false,},
            initialSort: [
                {column: "shortLimit", dir: "desc"},
            ],
            clipboard: true,
        };

        return option;
    },
});

Template.TradingLimitViewerTmpl.events({
    'click #requestDataButton': function (event, template) {
        for (const client of FEPClientCenter.getAllFEPClient())
            client.todayTotalQuantityRequest();

        template.updateGreeks();
        event.stopPropagation();
    },

    'click #expiredMode': function (event, template) {
        template.expiredMode = document.getElementById("expiredMode").checked;
        template.updateDataVar();
        template.updateGraph();
        event.stopPropagation();
    },

    'click #autoRefresh': function (event, template) {
        template.refresh = document.getElementById("autoRefresh").checked;
        if (template.updateTimerId != null) {
            clearTimeout(template.updateTimerId);
            template.updateTimerId = null;
        }

        if (template.refresh)
            template.updateTimerId = template.startAutoRefresh(10_000);

        event.stopPropagation();
    },

    'submit .TradingLimitViewer form': function (event) {
        event.preventDefault();
    },
});
