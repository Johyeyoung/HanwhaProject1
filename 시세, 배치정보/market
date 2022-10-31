import {ReactiveVar} from 'meteor/reactive-var';

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

Template.MarketShareViewerTmpl.onCreated(function () {
    let self = this;
    FEPClientCenter.init();
    LiveSiseClient.init();

    self.getDateZeroTime = function (d) {
        return new Date(d.getFullYear(), d.getMonth(), d.getDate());
    };

    self.today = self.getDateZeroTime(new Date());
    self.equitydb = Meteor.subscribe("closingPriceEquityExtended", self.today);  //KR7
    self.futuredb = Meteor.subscribe("closingPriceFutures", self.today); //KR41,44,47
    self.optiondb = Meteor.subscribe("closingPriceOptions", self.today); //KR42,43
    self.marketsharedb = Meteor.subscribe("marketShare", self.today);
    self.accounttotalpricedb = Meteor.subscribe("accountTotalPrice", self.today);
    self.bookcodetotalpricedb = Meteor.subscribe("bookCodeTotalPrice", self.today);
    self.viewMode = "account";

    self.MarketShareView = new ReactiveVar({});
    self.MarketShareViewOption = new ReactiveVar(null);
    self.MarketShareData = [];
    self.MarketShareBookListVar = new ReactiveVar([]);
    self.TodayMarketView = new ReactiveVar([]);
    self.TodayMarketViewAccount = [];
    self.TodayMarketViewBookCode = [];
    self.TodayMarketViewOption = new ReactiveVar(null);
    self.liveMode = true;
    self.bookCode = "ALL";
    self.needToUpdate = new ReactiveVar(false);

    self.bookCodeSet = new Set();
    self.isinCodeSet = new Set();
    self.bookCodeFeeMap = new Map();

    self.getTodayMarketViewTabulator = function () {
        return Util.getTabulator("TodayMarketView");
    };

    self.customColumns = function () {
        let columns = [];
        let accountVisible = self.viewMode === "account";
        let bookCodeVisible = self.viewMode === "bookCode";

        columns.push({
            field: "location", title: "위치", width: 95,
            formatter: function (cell, formatterParams) {
                let data = cell.getValue();
                return self.getLocationString(data);
            }
        })
        columns.push({field: "accountNumber", title: "계좌번호", width: 150, hozAlign: "center", headerHozAlign: "center", visible : accountVisible});
        columns.push({field: "accountName", title: "계좌명", width: 230, hozAlign: "center", headerHozAlign: "center", visible : accountVisible});
        columns.push({field: "bookCode", title: "북코드", width: 150, hozAlign: "center", headerHozAlign: "center", visible : bookCodeVisible});
        columns.push({field: "bookName", title: "북이름", width: 170, hozAlign: "center", headerHozAlign: "center", visible : bookCodeVisible});
        columns.push({
            field: "totalPrice", title: "누적거래대금", width: 180, hozAlign: "center", headerHozAlign: "center",
            formatter: function (cell, formatterParams) {
                let data = cell.getValue();
                return Util.formatNumber(data, true, true, 0, false);
            }
        });
        columns.push({
            field: "bookCodeFee", title: "총수수료", width: 140, hozAlign: "center", headerHozAlign: "center", visible: bookCodeVisible,
            formatter: function (cell, formatterParams) {
                let data = cell.getValue();
                return Util.formatNumber(data, true, true, 0, false);
            }
        });

        return columns;
    };

    self.updateTodayMarketViewTabulator = function (columnsUpdate) {
        if (columnsUpdate === true) {
            let columns = self.customColumns();
            let tabulator = self.getTodayMarketViewTabulator();
            tabulator.setColumns(columns);
        }

        self.updateTodayMarketViewBookCode();

        let data = (self.viewMode === "bookCode") ? self.TodayMarketViewBookCode : self.TodayMarketViewAccount;
        self.TodayMarketView.set(data);
    };

    self.updateTodayMarketViewBookCode = function () {
        let viewData = [];
        let data = self.TodayMarketViewBookCode;
        for (const info of data) {
            let key = info.location + '_' + info.bookCode;
            if (self.bookCodeFeeMap.has(key))
                info.bookCodeFee = self.bookCodeFeeMap.get(key);
            viewData.push(info);
        }
        self.TodayMarketViewBookCode = viewData;
    };

    self.updateFluctuation = function (){
        let tabulator = self.getTabulatorObject();
        let rows = tabulator.getRows();
        self.reactiveData = [];

        for (const row of rows){
            let json = row.getData();
            json['fluctuation'] = self.calcFluctuation(json['isinCode'], json['theoPrice']);
            self.reactiveData.push(json);
        }
        tabulator.updateData(self.reactiveData);
        tabulator.redraw(true);
    };

    self.clearTable = function () {
        self.MarketShareView.set([]);
        self.TodayMarketView.set([]);
        self.TodayMarketViewAccount = [];
        self.TodayMarketViewBookCode = [];
        self.bookCodeSet = new Set();
        self.isinCodeSet = new Set();
    };

    self.getDateString = function (d) {
        let result = "";
        result += d.getFullYear();
        result += "-";

        if (d.getMonth() < 9)
            result += "0";
        result += (d.getMonth() + 1);
        result += "-";

        if (d.getDate() < 10)
            result += "0";
        result += d.getDate();

        return result;
    };

    self.getLocationString = function (str) {
        if (str === "SEOUL")
            return "서울";
        else if (str === "PUSAN")
            return "부산";
        else
            return str;
    };

    self.calcFee = function (info) {
        let type = ItemMaster.isEquity(info.isinCode) ? "Equity" : "Deriv";
        let itemInfo = (type === "Equity") ? ItemMaster.getEquityItemInfo(info.isinCode) : ItemMaster.getFuturesItemInfo(info.isinCode);
        let feeInfo = ItemMaster.getFeeInfo(info.isinCode);
        if (itemInfo === null || feeInfo.length === 0)
            return 0;
        let price = itemInfo.hasOwnProperty("기준가격") ? itemInfo.기준가격 : itemInfo.기준가;
        let fee = feeInfo[0].tradingFee + feeInfo[0].clearingFee + feeInfo[0].depositoryFee;

        let longQty = 0, shortQty = 0, longAmt = 0, shortAmt = 0;
        let multiplier = itemInfo.hasOwnProperty("multiplier") ? itemInfo.multiplier : 1;
        longQty = self.bidQuantityCushion(info) * multiplier;
        shortQty = self.numberCushion(info.askQuantity) * multiplier;
        longAmt += longQty * price;
        shortAmt += shortQty * price;
        let longFeeAmt = longAmt * fee * 0.01;
        let shortFeeAmt = shortAmt * fee * 0.01;
        let feeAmt = longFeeAmt + shortFeeAmt;
        return feeAmt;
    };

    self.calcBookCodeFee = function () {
        self.bookCodeFeeMap = new Map();
        for (const data of self.MarketShareData) {
            let key = data.location + '_' + data.bookCode.replace(' ', '');
            let bookCodeFeeAmt = self.bookCodeFeeMap.has(key) ? self.bookCodeFeeMap.get(key) : 0;
            if (data.fee !== undefined)
                bookCodeFeeAmt += data.fee;
            self.bookCodeFeeMap.set(key, bookCodeFeeAmt);
        }
    };

    self.locationCushion = function (l) {
        return (l === undefined || l.location === null ? "" : l);
    };

    self.numberCushion = function (n) {
        return (n === undefined ? 0 : n);
    };

    self.bookQuantityCushion = function (row) {
        if (row.bookQuantity === undefined)
            return row.bidQuantity + row.askQuantity;
        else
            return row.bookQuantity;
    };

    self.bidQuantityCushion = function (row) {
        if (row.bidQuantity === undefined)
            return row.bookQuantity;
        else
            return row.bidQuantity;
    };

    self.getMarketQuantity = function (isinCode) {
        let type = isinCode.substring(0, 4);
        let futurePrefix = ["KR41", "KR44", "KR47"];
        let optionPrefix = ["KR42", "KR43"];

        let data;

        if (futurePrefix.includes(type))
            data = ClosingPriceFutures.findOne({isinCode: isinCode}, {fields: {totalContractAmount: true}});
        else if (optionPrefix.includes(type))
            data = ClosingPriceOptions.findOne({isinCode: isinCode}, {fields: {totalContractAmount: true}});
        else
            data = ClosingPriceEquityExtended.findOne({isinCode: isinCode}, {fields: {totalContractAmount: true}});

        if (data !== undefined && data.totalContractAmount !== undefined)
            return data.totalContractAmount;

        return 0;
    };

    self.setMarketShareByBookCode = function () {
        let ViewData = [];
        let bookCode = self.bookCode;

        if (bookCode.trim() === "ALL") {
            document.getElementById("marketShareBookName").text = "ALL";
            self.MarketShareView.set(self.MarketShareData);
            return;
        }

        document.getElementById("marketShareBookName").innerText = BookMaster.getBookName(bookCode);

        for (const data of self.MarketShareData)
            if (data.bookCode === bookCode)
                ViewData.push(data);

        self.MarketShareView.set(ViewData);
    };

    self.loadMarketShare = function (date) {
        let data = MarketShare.find({date}).fetch();
        let ViewData = [];

        let bookCodeSet = new Set();
        let isinCodeSet = new Set();

        for (const info of data) {
            let marketTotalQuantity = 0;
            if (!self.liveMode)
                marketTotalQuantity = self.getMarketQuantity(info.isinCode);

            let bookShare = 0.0;
            let marketShare = 0.0;

            if (info.totalQuantity !== 0)
                bookShare = self.bookQuantityCushion(info) / info.totalQuantity * 100;

            if (marketTotalQuantity !== 0)
                marketShare = self.bookQuantityCushion(info) / marketTotalQuantity * 100;

            let badMakeAmount, takeAmount, goodMakeAmount, marketAmount;
            badMakeAmount = takeAmount = goodMakeAmount = marketAmount = 0;
            if (info.hasOwnProperty("contractTypeSummary")) {
                badMakeAmount = info.contractTypeSummary.badMakeAmount;
                takeAmount = info.contractTypeSummary.takeAmount;
                goodMakeAmount = info.contractTypeSummary.goodMakeAmount;
                marketAmount = info.contractTypeSummary.marketAmount;
            } else if (info.hasOwnProperty("badMakeAmount")) { // for DB data
                badMakeAmount = info.badMakeAmount;
                takeAmount = info.takeAmount;
                goodMakeAmount = info.goodMakeAmount;
                marketAmount = info.marketAmount;
            }

            bookCodeSet.add(info.bookCode);
            isinCodeSet.add(info.isinCode);

            ViewData.push({
                location: self.locationCushion(info.location),
                isinCode: info.isinCode,
                issueName: ItemMaster.getProductName(info.isinCode),
                bookCode: info.bookCode,
                bookName: BookMaster.getBookName(info.bookCode),
                bookQuantity: self.bookQuantityCushion(info),
                bidQuantity: self.bidQuantityCushion(info),
                askQuantity: self.numberCushion(info.askQuantity),
                MMTeamTotalQuantity: info.totalQuantity,
                marketTotalQuantity: marketTotalQuantity,
                bookShare: bookShare,
                marketShare: marketShare,
                badMakeRatio: badMakeAmount * 100 / info.totalQuantity,
                goodMakeRatio: goodMakeAmount * 100 / info.totalQuantity,
                takeRatio: takeAmount * 100 / info.totalQuantity,
                marketRatio: marketAmount * 100 / info.totalQuantity,
                fee: self.calcFee(info),
            })
        }

        self.MarketShareData = ViewData;
        self.MarketShareView.set(ViewData);

        document.getElementById("countLabel").innerText = "종목 개수 : " + isinCodeSet.size + "개";

        let bookCodeData = [{bookCode: "ALL", bookName: "ALL"}];
        bookCodeSet.forEach((value, dummyValue, setObject) => bookCodeData.push({
            bookCode: value,
            bookName: BookMaster.getBookName(value)
        }));
        self.calcBookCodeFee();
        self.MarketShareBookListVar.set(bookCodeData);
    };

    self.loadAccountTotalPrice = function (date) {
        let data = AccountTotalPrice.find({date}).fetch();
        let ViewData = [];

        for (const info of data) {
            ViewData.push({
                location: self.locationCushion(info.location),
                accountNumber: info.account,
                accountName: AccountMaster.getAccountName(info.account),
                totalPrice: info.totalPrice
            });
        }
        self.TodayMarketViewAccount = ViewData;
    };

    self.loadBookCodeTotalPrice = function (date) {
        let data = BookCodeTotalPrice.find({date}).fetch();
        let ViewData = [];

        for (const info of data) {
            ViewData.push({
                location: self.locationCushion(info.location),
                bookCode: info.bookCode,
                bookName: BookMaster.getBookName(info.bookCode),
                totalPrice: info.totalPrice,
                bookCodeFee: self.bookCodeFeeMap.get(self.locationCushion(info.location) + '_' + info.bookCode.replace(' ', ''))
            });
        }
        self.TodayMarketViewBookCode = ViewData;
    };

    for (const client of FEPClientCenter.getAllFEPClient()) {
        client.init();
        client.registerHandler("todayTotalQuantityData", "FEPServerResponse", this, async function (obj, template, client) {
            if (obj.trCode !== "FEPServerResponse") {
                console.log("FEPServerResponse가 요청하지 않은 응답은 무시합니다.");
                console.log(obj);
                return;
            }

            let ViewData = template.MarketShareView.get();
            let bookCodeSet = self.bookCodeSet;
            let isinCodeSet = self.isinCodeSet;

            for (const info of obj.totalQuantityList) {
                let marketTotalQuantity = template.getMarketQuantity(info.isinCode);
                let bookShare = 0.0;
                let marketShare = 0.0;

                if (info.totalQuantity !== 0)
                    bookShare = self.bookQuantityCushion(info) / info.totalQuantity * 100;

                if (marketTotalQuantity !== 0)
                    marketShare = self.bookQuantityCushion(info) / marketTotalQuantity * 100;

                let badMakeAmount, takeAmount, goodMakeAmount, marketAmount;
                badMakeAmount = takeAmount = goodMakeAmount = marketAmount = 0;
                if (info.hasOwnProperty("contractTypeSummary")) {
                    badMakeAmount = info.contractTypeSummary.badMakeAmount;
                    takeAmount = info.contractTypeSummary.takeAmount;
                    goodMakeAmount = info.contractTypeSummary.goodMakeAmount;
                    marketAmount = info.contractTypeSummary.marketAmount;
                }

                bookCodeSet.add(info.bookCode);
                isinCodeSet.add(info.isinCode);

                ViewData.push({
                    location: client.getServerId(),
                    isinCode: info.isinCode,
                    issueName: ItemMaster.getProductName(info.isinCode),
                    bookCode: info.bookCode,
                    bookName: BookMaster.getBookName(info.bookCode),
                    bookQuantity: self.bookQuantityCushion(info),
                    bidQuantity: self.bidQuantityCushion(info),
                    askQuantity: self.numberCushion(info.askQuantity),
                    MMTeamTotalQuantity: info.totalQuantity,
                    marketTotalQuantity: marketTotalQuantity,
                    bookShare: bookShare,
                    marketShare: marketShare,
                    badMakeRatio: badMakeAmount * 100 / info.totalQuantity,
                    goodMakeRatio: goodMakeAmount * 100 / info.totalQuantity,
                    takeRatio: takeAmount * 100 / info.totalQuantity,
                    marketRatio: marketAmount * 100 / info.totalQuantity,
                    fee: self.calcFee(info),
                });
            }

            let isinCodeList = [];
            for (const isinCode of isinCodeSet)
                isinCodeList.push(isinCode);

            LiveSiseClient.liveTotalQuantityRequest(isinCodeList);

            document.getElementById("countLabel").innerText = "종목 개수 : " + isinCodeSet.size + "개";

            let bookCodeData = [{bookCode: "ALL", bookName: "ALL"}];
            bookCodeSet.forEach((value, dummyValue, setObject) => bookCodeData.push({
                bookCode: value,
                bookName: BookMaster.getBookName(value)
            }));
            template.calcBookCodeFee();
            template.updateTodayMarketViewTabulator();

            template.MarketShareData = ViewData;
            template.needToUpdate.set(true);
            template.MarketShareBookListVar.set(bookCodeData);
        });

        client.registerHandler("accountTotalPriceData", "FEPServerResponse", this, function (obj, template, client) {
            if (obj.trCode !== "FEPServerResponse") {
                console.log("FEPServerResponse가 요청하지 않은 응답은 무시합니다.");
                console.log(obj);
                return;
            }

            let ViewData = template.TodayMarketViewAccount;

            for (const info of obj.totalPriceList) {
                ViewData.push({
                    location: client.getServerId(),
                    accountNumber: info.account,
                    accountName: AccountMaster.getAccountName(info.account),
                    totalPrice: info.totalPrice
                });
            }
            template.TodayMarketViewAccount = ViewData;
            template.updateTodayMarketViewTabulator();
        });

        client.registerHandler("bookCodeTotalPriceData", "FEPServerResponse", this, function (obj, template, client) {
            if (obj.trCode !== "FEPServerResponse") {
                console.log("FEPServerResponse가 요청하지 않은 응답은 무시합니다.");
                console.log(obj);
                return;
            }

            let ViewData = template.TodayMarketViewBookCode;

            for (const info of obj.totalPriceList) {
                ViewData.push({
                    location: client.getServerId(),
                    bookCode: info.bookCode,
                    bookName: BookMaster.getBookName(info.bookCode),
                    totalPrice: info.totalPrice,
                    bookCodeFee: self.bookCodeFeeMap.get(client.getServerId() + '_' + info.bookCode.replace(' ', ''))
                });
            }
            template.TodayMarketViewBookCode = ViewData;
            template.updateTodayMarketViewTabulator();
        });
    }

    LiveSiseClient.registerHandler("LiveTotalQuantityData", this, function (obj, template) {
        console.log("LiveTotalQuantityData");
        let Qmap = new Map();

        for (const info of obj.totalQuantityList)
            Qmap.set(info.isinCode, info.totalQuantity);

        let rawViewData = template.MarketShareData;
        let ViewData = [];

        for (const info of rawViewData) {
            if (Qmap.has(info.isinCode)) {
                info.marketTotalQuantity = Qmap.get(info.isinCode);
                info.marketShare = info.bookQuantity / info.marketTotalQuantity * 100;
            }
            ViewData.push(info);
        }

        template.MarketShareData = ViewData;
        template.needToUpdate.set(true);
    });
});

Template.MarketShareViewerTmpl.onRendered(function () {
    this.autorun(() => {
        let self = Template.instance();
        if (self.equitydb.ready() &&
            self.futuredb.ready() &&
            self.optiondb.ready() &&
            self.marketsharedb.ready() &&
            self.accounttotalpricedb.ready() &&
            self.bookcodetotalpricedb.ready() &&
            Util.isItemMasterReady()) {
            self.clearTable();
            for (const client of FEPClientCenter.getAllFEPClient()) {
                client.todayTotalQuantityRequest();
                client.totalPriceRequest("account");
                client.totalPriceRequest("bookCode");
            }

            $('#datePicker').datetimepicker({format: "YYYY-MM-DD", defaultDate: null});
            //loadMarketShare();
            //loadAccountTotalPrice();
            //loadBookCodeTotalPrice();
        }
    });

    this.autorun(() => {
        let template = Template.instance();
        let needToUpdate = template.needToUpdate.get();

        if (needToUpdate) {
            template.setMarketShareByBookCode();
            template.needToUpdate.set(false);
        }
    });
});

Template.MarketShareViewerTmpl.onDestroyed(function () {
    for (const client of FEPClientCenter.getAllFEPClient()) {
        client.unregisterHandler("todayTotalQuantityData", "FEPServerResponse");
        client.unregisterHandler("accountTotalPriceData", "FEPServerResponse");
        client.unregisterHandler("bookCodeTotalPriceData", "FEPServerResponse");
    }

    LiveSiseClient.unregisterHandler("LiveTotalQuantityData");
});

Template.MarketShareViewerTmpl.helpers({

    bookList: function () {
        let self = Template.instance();
        return self.MarketShareBookListVar.get();
    },

    reactiveMarketShareView: function () {
        let self = Template.instance();
        let data = self.MarketShareView.get();
        self.MarketShareViewOption.set({dataArray: data});
        return self.MarketShareViewOption;
    },

    reactiveTodayMarketView: function () {
        let self = Template.instance();
        let data = self.TodayMarketView.get();
        self.TodayMarketViewOption.set({dataArray: data});
        return self.TodayMarketViewOption;
    },

    optionsMarketShareView: function () {
        let self = Template.instance();
        let option = {
            columnHeaderVertAlign: "bottom",
            height: 600,
            reactiveData: true,
            data: self.TodayMarketViewOption,
            columns: [
                {
                    field: "location", title: "위치", width: 95, headerHozAlign: "center",
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return self.getLocationString(data);
                    }
                },
                {field: "isinCode", title: "종목코드", hozAlign: "center", visible: false},
                {field: "issueName", title: "종목명", hozAlign: "center", headerHozAlign: "center", width: 200},
                {field: "bookCode", title: "북코드", hozAlign: "center", visible: false},
                {field: "bookName", title: "북이름", hozAlign: "center", headerHozAlign: "center", width: 130},
                {
                    title: "거래량",
                    columns: [
                        {
                            field: "bookQuantity", title: "북", hozAlign: "center", visible: false, width: 90,
                            formatter: function (cell, formatterParams) {
                                let data = cell.getValue();
                                return Util.formatNumber(data, true, true, 0, false);
                            }
                        },
                        {
                            field: "bidQuantity", title: "매수", hozAlign: "center", headerHozAlign: "center", width: 90,
                            formatter: function (cell, formatterParams) {
                                let data = cell.getValue();
                                return Util.formatNumber(data, true, true, 0, false);
                            }
                        },
                        {
                            field: "askQuantity", title: "매도", hozAlign: "center", headerHozAlign: "center", width: 90,
                            formatter: function (cell, formatterParams) {
                                let data = cell.getValue();
                                return Util.formatNumber(data, true, true, 0, false);
                            }
                        },
                        {
                            field: "MMTeamTotalQuantity", title: "MM팀", hozAlign: "center", width: 90, visible: false,
                            formatter: function (cell, formatterParams) {
                                let data = cell.getValue();
                                return Util.formatNumber(data, true, true, 0, false);
                            }
                        },
                        {
                            field: "marketTotalQuantity",
                            title: "시장",
                            hozAlign: "center",
                            headerHozAlign: "center",
                            width: 90,
                            formatter: function (cell, formatterParams) {
                                let data = cell.getValue();
                                return Util.formatNumber(data, true, true, 0, false);
                            }
                        },
                    ],
                },
                {
                    title: "점유율",
                    columns: [
                        {
                            field: "bookShare",
                            title: "북",
                            hozAlign: "center",
                            headerHozAlign: "center",
                            visible: false,
                            width: 70,
                            formatter: function (cell, formatterParams) {
                                let data = cell.getValue();
                                return Util.formatNumber(data, true, true, 2, false) + "%"
                            }
                        },
                        {
                            field: "marketShare", title: "시장", hozAlign: "center", headerHozAlign: "center", width: 70,
                            formatter: function (cell, formatterParams) {
                                let data = cell.getValue();
                                return Util.formatNumber(data, true, true, 2, false) + "%"
                            }
                        },
                    ],
                },

                {
                    field: "badMakeRatio", title: "Bad", hozAlign: "center", headerHozAlign: "center", width: 70,
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.formatNumber(data, true, true, 2, false) + "%"
                    }
                },
                {
                    field: "goodMakeRatio", title: "Good", hozAlign: "center", headerHozAlign: "center", width: 70,
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.formatNumber(data, true, true, 2, false) + "%"
                    }
                },
                {
                    field: "takeRatio", title: "Take", hozAlign: "center", headerHozAlign: "center", width: 70,
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.formatNumber(data, true, true, 2, false) + "%"
                    }
                },
                {
                    field: "marketRatio",
                    title: "Market",
                    hozAlign: "center",
                    headerHozAlign: "center",
                    visible: false,
                    width: 70,
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.formatNumber(data, true, true, 2, false) + "%"
                    }
                },
                {
                    field: "fee",
                    title: "수수료",
                    hozAlign: "center",
                    headerHozAlign: "center",
                    width: 100,
                    formatter: function (cell, formatterParams) {
                        let data = cell.getValue();
                        return Util.formatNumber(data, true, true, 0, false);
                    }
                },
            ],
            keybindings: {"copyToClipboard": false,},
            clipboard: true,
        }
        return option;
    },

    optionsTodayMarketView: function () {
        let self = Template.instance();
        let height = 600;
        let columns = self.customColumns();
        let option = {
            columns: columns,
            height: height,
            layout: "fitDataFill",
            keybindings: {"copyToClipboard": false,},
            clipboard: true,
        }
        return option;
    },

    isDBReady: function () {
        let self = Template.instance();

        return !!(self.equitydb.ready() &&
            self.futuredb.ready() &&
            self.optiondb.ready() &&
            self.marketsharedb.ready() &&
            self.accounttotalpricedb.ready() &&
            self.bookcodetotalpricedb.ready() &&
            Util.isItemMasterReady());
    },
});

Template.MarketShareViewerTmpl.events({
    'click #toggleButton': function (event, template) {
        if (template.liveMode) {
            template.liveMode = false;
            document.getElementById("modeLabel").innerText = "Mode : DB";
            document.getElementById("dateTextBox").disabled = false;
            document.getElementById("searchButton").disabled = false;
            document.getElementById("refreshButton").disabled = true;

            if (document.getElementById("dateTextBox").value === "")
                document.getElementById("dateTextBox").value = template.getDateString(new Date());
        } else {
            template.liveMode = true;
            document.getElementById("modeLabel").innerText = "Mode : Live";
            document.getElementById("dateTextBox").disabled = true;
            document.getElementById("searchButton").disabled = true;
            document.getElementById("refreshButton").disabled = false;

            template.clearTable();
            for (const client of FEPClientCenter.getAllFEPClient()) {
                client.todayTotalQuantityRequest();
                client.totalPriceRequest("account");
                client.totalPriceRequest("bookCode");
            }
        }

        event.stopPropagation();
    },

    'click #searchButton': async function (event, template) {
        let date = template.getDateZeroTime(new Date(document.getElementById("dateTextBox").value));

        console.log(date);

        template.equitydb = Meteor.subscribe("closingPriceEquityExtended", date);  //KR7
        template.futuredb = Meteor.subscribe("closingPriceFutures", date); //KR41,44,47
        template.optiondb = Meteor.subscribe("closingPriceOptions", date); //KR42,43
        template.marketsharedb = Meteor.subscribe("marketShare", date);
        template.accounttotalpricedb = Meteor.subscribe("accountTotalPrice", date);
        template.bookcodetotalpricedb = Meteor.subscribe("bookCodeTotalPrice", date);

        template.clearTable();

        while (!(template.equitydb.ready() &&
            template.futuredb.ready() &&
            template.optiondb.ready() &&
            template.marketsharedb.ready() &&
            template.accounttotalpricedb.ready() &&
            template.bookcodetotalpricedb.ready())) {
            await sleep(200);

            document.getElementById("dbLabel").innerText = "DB Loading...";

            if (template.equitydb.ready() &&
                template.futuredb.ready() &&
                template.optiondb.ready() &&
                template.marketsharedb.ready() &&
                template.accounttotalpricedb.ready() &&
                template.bookcodetotalpricedb.ready()) {

                document.getElementById("dbLabel").innerText = "";
                template.loadMarketShare(date);
                template.loadAccountTotalPrice(date);
                template.loadBookCodeTotalPrice(date);
                template.updateTodayMarketViewTabulator();
                break;
            }
        }

        event.stopPropagation();
    },

    'click .marketShareBookCond': function (event, template) {
        template.bookCode = event.currentTarget.getAttribute("data-bookcode");
        template.setMarketShareByBookCode();
    },

    'click #refreshButton': function (event, template) {
        template.clearTable();

        for (const client of FEPClientCenter.getAllFEPClient()) {
            client.todayTotalQuantityRequest();
            client.totalPriceRequest("account");
            client.totalPriceRequest("bookCode");
        }

        event.stopPropagation();
    },

    'click .radio-inline': function (event, template) {
        template.viewMode = event.currentTarget.getElementsByTagName("input")[0].value;
        template.updateTodayMarketViewTabulator(true);
    },

    'submit .marketShareViewer form': function (event, template) {
        event.preventDefault();
    },
});
