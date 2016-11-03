#!/usr/bin/python
"""
Generate CSV and SWIFT files for FISERV tests
"""
import sys, random, time, getopt
from datetime import date
import datetime

PERCENT_TAB = [1, 2, 3, 4, 5, 15, 30, 40]
TRANSAC_TAB = [1, 0.8, 0.6, 0.4, 0.2, 0.1, 0.05, 0.01]
CURRENCIES = ['EUR']

def usage():
    """
    Show the help message
    """
    print """\
Generation usage : 
            -c <counterpart_number>       : set the number of counterparts (must be a multiple of 100)
            -t <max_transaction>          : set the maximum transaction number (must be a multiple of 100)
            -d <days_number>              : set the number of days with no aggregation
            -h                            : show help message
"""

def main():
    """
    Main function
    """
    ctp_n, max_transac_n, max_days = 0, 0, 1

    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hc:t:d:")
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-c":
            ctp_n = int(arg)
        elif opt == "-t":
            max_transac_n = int(arg)
        elif opt == "-d":
            max_days = int(arg)
        elif opt == "-h":
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    for day in xrange(1, max_days + 1):
        dat = date(2010, 4, 29) + datetime.timedelta(days=day)
        creation = Creation(ctp_n, max_transac_n, dat)
        creation.execution()

class Creation(object):
    """
    Creation class that will generate everything for a date
    """

    def __init__(self, ctp_n, max_transac_n, dat):
        self.ctp_n = ctp_n
        self.max_transac_n = max_transac_n
        self.date = dat

        start = time.time()
        self.counterparts = self.create_counterparts()
        end = time.time()

        create_ctp_time = end - start
        print "Counterparts creation took : {}s".format(create_ctp_time)
        sys.stdout.flush()

    def execution(self):
        """
        Main execution function
        """
        start = time.time()
        self.create_cash_csv_file()
        self.create_rec_csv_file()
        end = time.time()

        create_csv_time = end - start
        print "CSVs creation took : {}s".format(create_csv_time)
        sys.stdout.flush()

        start = time.time()
        for key, value in self.counterparts.iteritems():
            self.create_swift_file(key, 'EUR', '9400120142730122', value)
        end = time.time()

        create_swifts_time = end - start
        print "Swifts creation took : {}s".format(create_swifts_time)
        sys.stdout.flush()

        self.valid()

    def valid(self):
        """
        Valid the balance betweens transactions and counterparts
        """
        count = [0, 0, 0, 0, 0, 0, 0, 0]

        for ctp in self.counterparts:
            t_number = len(self.counterparts[ctp]) / float(self.max_transac_n)
            count[TRANSAC_TAB.index(t_number)] += 1

        for i in range(0, len(count)):
            count[i] = count[i] * 100 / self.ctp_n

        res1, res2 = self.get_size(), 0

        for ctp in self.counterparts:
            res2 += len(self.counterparts[ctp])

        if count == PERCENT_TAB and res1 == res2:
            print "Result is valid"
        elif count != PERCENT_TAB:
            print """\
        count is different from PERCENT_TAB :
        count : {}
        PERCENT_TAB ! {}
        """.format(count, PERCENT_TAB)
        else:
            print """\
        res1 and res2 are different :
        res1 : {}
        res2 : {}
        """.format(res1, res2)

    def get_per_index(self, val):
        """
        Get the current index from PERCENT_TAB with the index of the current
        counterpart
        """
        summ = 0
        val = float(val + 1) / float(self.ctp_n) * 100.0
        for i, per in enumerate(PERCENT_TAB):
            summ += per
            if val <= summ:
                return i

    def get_size(self):
        """
        Return the total transaction number
        """
        size = 0

        for index, per in enumerate(PERCENT_TAB):
            tmp = self.ctp_n * per / 100
            tmp = tmp * TRANSAC_TAB[index] * self.max_transac_n
            size += tmp
        return int(size)

    def create_counterparts(self):
        """
        Temporary method to remove create counterparts to increase speed
        """
        size = self.get_size()

        counterparts = {}
        ran = range(0, self.ctp_n)
        tmp = ['CTP_' + str(n + 1) + '_' + CURRENCIES[0] for n in ran]
        tmp = random.sample(tmp, self.ctp_n)

        for elem in tmp:
            counterparts[elem] = {}

        flow_ids = random.sample(xrange(1, size + 2), size + 1)
        t_vals = random.sample(xrange(1, 1000 * self.max_transac_n), size + 1)

        for i, name in enumerate(counterparts):
            per_index = self.get_per_index(i)
            nb_tran = int(TRANSAC_TAB[per_index] * self.max_transac_n)
            for _ in range(0, nb_tran):
                val = t_vals.pop() * (-1) ** random.randint(0, 1)
                counterparts[name][flow_ids.pop()] = val

        return counterparts

    def create_cash_csv_file(self):
        """
        Create the csv file with the list of accounts
        """
        csv_account_file = open("cash_accounts.csv", 'w')

        for ctp in self.counterparts:
            csv_account_file.write("{0},{0},EUR,Bank\
,Cash,{0},MUREX\n".format(ctp))

    def create_rec_csv_file(self):
        """
        Create the csv file with the list of transactions
        """
        dat = self.date.strftime("%d%m%y")
        csv_rec_file = open('cash_rec_{}.csv'.format(dat), 'w')
        csv_rec_file.write('flowId,status,account,currency,vdate,rdate' +
                           ',amount,PR,type,legEntity,counterparty' +
                           ',dfStatus,cntOrigin,dfRev,recFlowId\n')

        for ctp in self.counterparts:
            for flow in self.counterparts[ctp]:
                self.write_rec_line(csv_rec_file, ctp, flow)

    def write_rec_line(self, csv_rec_file, ctp, flow):
        """
        Write in csv_rec_file the line of a transaction
        """
        csv_rec_file.write("\
{1},SentToRec,{0},{2}\
,{5},{5},{3}\
,{4},Outright,MUREX,BARCLAYS BANK PLC,Released\
,{0},,{1}\n".format(ctp, flow, CURRENCIES[0],
                    abs(self.counterparts[ctp][flow]),
                    'R' if self.counterparts[ctp][flow] > 0 else 'P',
                    self.date.strftime("%d/%m/%y")))

    def create_swift_file(self, counterpart_name, currency, transaction_n, trs):
        """
        Create a swift file, it's call for each counterparts
        """
        dat = self.date.strftime("%y%m%d")
        dat2 = self.date.strftime("%m%d")
        name = "MT940-{}-{}.txt".format(counterpart_name, dat)
        swift_file = open(name, 'w')
        swift_first_part = ("""\
{{1:F01            0000000000}}{{2:O9400000{3}            0000000000{3}0545N}}{{4:
:20:{0}
:21:20{3}000000
:25:{1}
:28C:1/1
:60F:C{3}{2}0,00\n""".format(transaction_n, counterpart_name, currency, dat))
        swift_file.write(swift_first_part)

        for tra in trs:
            swift_file.write("""\
:61:{}{}{}D{},00NTRF{}
Spot and Fees\n""".format(dat, dat2, 'C' if trs[tra] > 0 else 'D',
                          abs(trs[tra]), tra))

        swift_file.write(":62F:C{}EUR{},00\
\n".format(dat, sum(trs[i] for i in trs)) +
                         "-}")

if __name__ == "__main__":
    main()
