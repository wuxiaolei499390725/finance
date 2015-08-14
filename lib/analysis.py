import sys
import os
import datetime
p = os.path.dirname(os.path.abspath(__file__))
if p in sys.path:
    pass
else:
    sys.path.append(p)
from file_io import FileIO
from ti import TechnicalIndicators
from classifier import Classifier
from regression import Regression
from draw import Draw

class Analysis():

    def __init__(self, code="", name="", start='2014-09-01',
                 days=180, csvfile=None, update=False,
                 axis=2,
                 reference=[]):
        self.code = code
        self.name = name
        self.start = start
        self.end = datetime.datetime.now()
        self.days = int(days) * -1
        self.csvfile = csvfile
        self.update = update
        self.clffile = "".join(['clf_', code, '.pickle'])
        self.regfile = "".join(['reg_', code, '.pickle'])
        if axis:
            self.axis = int(axis)
        else:
            self.axis = 2
        self.reference = reference

    def run(self):
        io = FileIO()
        will_update = self.update

        if self.csvfile:
            stock_tse = io.read_from_csv(self.code,
                                         self.csvfile)

            msg = "".join(["Read data from csv: ", self.code,
                           " Records: ", str(len(stock_tse))])
            print(msg)

            if self.update and len(stock_tse) > 0:
                t = stock_tse.index[-1].strftime('%Y-%m-%d')
                newdata = io.read_data(self.code,
                                       start=t,
                                       end=self.end)

                msg = "".join(["Read data from web: ", self.code,
                               " New records: ", str(len(newdata))])
                print(msg)
                if len(newdata) < 2:
                    will_update = False

                stock_tse = stock_tse.combine_first(newdata)
                io.save_data(stock_tse, self.code, 'stock_')
        else:
            stock_tse = io.read_data(self.code,
                                     start=self.start,
                                     end=self.end)

            msg = "".join(["Read data from web: ", self.code,
                           " Records: ", str(len(stock_tse))])
            print(msg)

        if stock_tse.empty:
            msg = "".join(["Data empty: ", self.code])
            print(msg)
            return None

        if not self.csvfile:
            io.save_data(stock_tse, self.code, 'stock_')

        try:
            stock_d = stock_tse.asfreq('B').dropna()[self.days:]

            ti = TechnicalIndicators(stock_d)

            ti.calc_sma()
            ti.calc_sma(timeperiod=5)
            ti.calc_sma(timeperiod=25)
            ti.calc_sma(timeperiod=50)
            ti.calc_sma(timeperiod=75)
            ewma = ti.calc_ewma(span=5)
            ewma = ti.calc_ewma(span=25)
            ewma = ti.calc_ewma(span=50)
            ewma = ti.calc_ewma(span=75)
            bbands = ti.calc_bbands()
            sar = ti.calc_sar()
            draw = Draw(self.code, self.name)

            ret = ti.calc_ret_index()
            ti.calc_vol(ret['ret_index'])
            rsi = ti.calc_rsi(timeperiod=9)
            rsi = ti.calc_rsi(timeperiod=14)
            mfi = ti.calc_mfi()
            roc = ti.calc_roc(timeperiod=10)
            roc = ti.calc_roc(timeperiod=25)
            roc = ti.calc_roc(timeperiod=50)
            roc = ti.calc_roc(timeperiod=75)
            roc = ti.calc_roc(timeperiod=150)
            ti.calc_cci()
            ultosc = ti.calc_ultosc()
            stoch = ti.calc_stoch()
            ti.calc_stochf()
            ti.calc_macd()
            willr = ti.calc_willr()
            ti.calc_momentum(timeperiod=10)
            ti.calc_momentum(timeperiod=25)
            tr = ti.calc_tr()
            ti.calc_atr()
            ti.calc_natr()
            vr = ti.calc_volume_rate()

            ret_index = ti.stock['ret_index']
            clf = Classifier(self.clffile)
            train_X, train_y = clf.train(ret_index, will_update)
            msg = "".join(["Train Records: ", str(len(train_y))])
            print(msg)
            clf_result = clf.classify(ret_index)[0]
            msg = "".join(["Classified: ", str(clf_result)])
            print(msg)
            ti.stock.ix[-1, 'classified'] = clf_result

            reg = Regression(self.regfile,
                             alpha=1,
                             regression_type="Ridge")
            train_X, train_y = reg.train(ret_index, False)
            msg = "".join(["Train Records: ", str(len(train_y))])
            base = ti.stock_raw['Adj Close'][0]
            reg_result = int(reg.predict(ret_index, base)[0])
            msg = "".join(["Predicted: ", str(reg_result)])
            print(msg)
            ti.stock.ix[-1, 'predicted'] = reg_result

            if len(self.reference) > 0:
                ti.calc_rolling_corr(self.reference)
                ref = ti.stock['rolling_corr']
            else:
                ref = []

            io.save_data(io.merge_df(stock_d, ti.stock),
                         self.code, 'ti_')

            draw.plot(stock_d, ewma, bbands, sar,
                      rsi, roc, mfi, ultosc, willr,
                      stoch, tr, vr,
                      clf_result, reg_result,
                      ref,
                      axis=self.axis)

            return ti

        except (ValueError, KeyError):
            msg = "".join(["Error occured in ", self.code])
            print(msg)
            return None
