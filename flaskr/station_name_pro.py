# coding: utf-8
import urllib2
import sys
import os
import json
import re
import sys
import collections
reload(sys)
sys.setdefaultencoding('utf8')

class stationInfo:

    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
        self.headers = {'User-Agent': self.user_agent}
        self.timeouts = 30
        self.station_version = "1.9042"
        self.station_means_requesturl = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version="+self.station_version
        #self.station_means_path = '/application/project/www/weixin/public/script/station_name/station_name.js'
        self.station_means_path = './station_name.js'

    def station_means_write(self):
        if not os.path.exists(self.station_means_path):
            with open(self.station_means_path, "ab") as filename:
                request2 = urllib2.Request(self.station_means_requesturl, headers=self.headers)
                response2 = urllib2.urlopen(request2, timeout=self.timeouts)
                content2 = response2.read()
                station_name = content2
                filename.write(station_name)

    # station code search
    def get_station_info(self, station):
        try:
            station_name = open(self.station_means_path).read()

            station_name = re.sub("';", "", re.sub("var station_names ='@", "", station_name)).split("@")

            station_rows = {}
            for station_row in station_name:
                station_rows[station_row.split("|")[1]] = station_row.split("|")

            station_now = [station_rows[row][2] for row in station_rows.keys() if station in row]
            return station_now
        except Exception, e:
            print e

    # station name search
    def get_station_name(self, code):
        station_name = open(self.station_means_path).read()
        station_name = re.sub("';", "", re.sub("var station_names ='@", "", station_name)).split("@")
        station_rows = {}
        for station_row in station_name:
            station_rows[station_row.split("|")[2]] = station_row.split("|")[1]

        return station_rows[code]

    # goout method
    def get_froms_tos(self, f_station, t_station):
        from_station = self.get_station_info(f_station)
        to_station = self.get_station_info(t_station)
        froms_tos = []
        for froms in from_station:
            for tos in to_station:
                froms_tos.append([froms, tos])
        return froms_tos

    def get_ticket_list(self, jsons):
        alldata = []

        for res in jsons["data"]["result"]:
            # print res.split("|")
            reslist = res.split("|")
            trainnum = reslist[3]
            froms = reslist[4]
            tos = reslist[5]
            froms_times = reslist[8]
            tos_times = reslist[9]
            all_times = reslist[10]
            zero_position = reslist[-5]
            first_position = reslist[-6]
            second_position = reslist[-7]
            soft_bed = reslist[-14]
            hard_bed = reslist[-9]
            soft_position = reslist[-13]
            hard_position = reslist[-8]
            none_position = reslist[-11]

            status = reslist[1]

            datas = collections.OrderedDict()
            datas["trainnum"] = trainnum
            datas["froms"] = self.get_station_name(froms)
            datas["tos"] = self.get_station_name(tos)
            datas["froms_times"] = froms_times
            datas["tos_times"] = tos_times
            datas["all_times"] = all_times
            datas["zero_position"] = zero_position
            datas["first_position"] = first_position
            datas["second_position"] = second_position
            datas["soft_bed"] = soft_bed
            datas["hard_bed"] = hard_bed
            datas["soft_position"] = soft_position
            datas["hard_position"] = hard_position
            datas["none_position"] = none_position
            datas["status"] = status

            alldata.append(datas)


        return alldata

    def station_validate(self, station):
        station_name = open(self.station_means_path).read()
        if station not in station_name:
            return False


    def _get(self, froms, tos, date):
        #means
        self.station_means_write()

        #验证
        self.station_validate(froms)
        self.station_validate(tos)
        froms_tos = self.get_froms_tos(froms, tos)
	#print froms_tos
        try:
            base_url = "https://kyfw.12306.cn/otn/leftTicket/queryZ?"
            leftTicketDTO_train_date = date
            leftTicketDTO_from_station = froms_tos[0][0]
            leftTicketDTO_to_station = froms_tos[0][1]
            purpose_codes = "ADULT"
            base_url += "leftTicketDTO.train_date=" + leftTicketDTO_train_date + "&leftTicketDTO.from_station=" + leftTicketDTO_from_station + "&leftTicketDTO.to_station=" + leftTicketDTO_to_station + "&purpose_codes=" + purpose_codes

            request = urllib2.Request(base_url, headers=self.headers)
            response = urllib2.urlopen(request, timeout=self.timeouts)
            content = response.read()
            jsons = json.loads(content)
            ticket_list = self.get_ticket_list(jsons)
            return ticket_list

        except Exception, e:
            if e == "No JSON object could be decoded":
                print None

    def _get_format_str(self, froms, tos, date):
        times = 0
        while True:
            times = times + 1
            res = sp._get(froms, tos, date)
            if res != None:
                allstr = ""
                u = 0
                for row in res:
                    # print row.values()
                    if u == 10:
                        break
                    allstr += " ".join(row.values()) + "\n"
                    u = u + 1
                break
            elif times == 10:
                allstr = "暂时查询不到车票信息，请稍后再试"
                break
        return allstr


if __name__ == "__main__":
    sp = stationInfo()
    print sp._get_format_str("北京", "广州", "2018-02-15")






