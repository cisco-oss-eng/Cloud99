from GraphData import graphData

class data_retriever(object):
    gDataDict = {}
    stime = None
    etime = None
    def __init__(self):
        self.gDataDict = {}

    def getTimeLineData(self,fileName):
        try:
            fp = open(fileName)
        except IOError as e:
            print "Error while opening the file %s...%s" % (fileName,e)
            return
        lines = fp.readlines()

        #gDataDict = {}
        for line in lines:
            if line.startswith("starttime"):
                self.stime = line.rstrip("\n").split("##")[1]
                continue
            elif line.startswith("endtime"):
                self.etime = line.rstrip("\n").split("##")[1]
                continue
            rec = line.rstrip("\n").split(",")
            #print len(rec)
                              
            host = rec[0]
            service = rec[1]
            ts = rec[2]
            status = rec[3]
            if len(rec) >= 5:
                desc = rec[4]
            else:
                desc = " "
            gData = graphData(host,service,desc,status,ts)
            if self.gDataDict.has_key(rec[0]+"##"+rec[1]):
                gDataList = self.gDataDict[rec[0]+"##"+rec[1]]
                gDataList.append(gData)
            else:
                gDataList = []
                gDataList.append(gData)
                self.gDataDict[rec[0]+"##"+rec[1]] = gDataList
        #print "Start Time : %s --- End Time : %s " % (self.stime,self.etime)
        data_retriever.printgDataDict(self.gDataDict)
    
    def getDataDict(self):
        return self.gDataDict
    
    def getSTime(self):
        return self.stime
    
    def getETime(self):
        return self.etime
    
    def caculateServiceStatePercent(self,timelinefile,archivefile):
        self.getTimeLineData(timelinefile)
        gDataDict = self.getDataDict()
        gData = []
        endTime = map(int,self.etime.split(' ')[1].split(':'))
    
        #print endTime
        for k in gDataDict.keys():
            temp = []
            # timemap ={}
            timemap=[]
            for item in gDataDict.get(k):
                temp_item =[]
                timemap.append(map(int,item.getTS().split(' ')[1].split(':')))
                temp_item.append(item.getHostName() + ' - ' + item.getServiceName())
                temp_item.append(item.getStatus())
                # temp.append('TS')
                temp_item.append(map(int,item.getTS().split(' ')[1].split(':')))
                temp.append(temp_item)
            count = 1
            #print timemap
            for i in temp:
            
                # print len(temp)
                # print 'count ',count
                if len(temp) == count:
                    i.append(endTime)
                else:
                    i.append(timemap[count])
                    count = count + 1    
            # print temp
            gData.extend(temp)
        #print gData
        '''
        for item in gData:
            if percDict.has_key(item[0]+item[1]):
                percList = percDict.get(item[0]+item[1])
                if item[1] == "OK":
                    sec = percList[0]
                    sec = sec +( item[3] - item[2] ) # This has to be fixed - rama go ahead
            else:
                percDict[item[0]+item[1]+item[2]]
        '''
        service_info = {}
        # hostname##servername:{'ok':time,'warning':time}, ...
        # [['NS','OK',[14,0,0],[14,15,0]],['NS','CRITICAL',[14,15,0],[14,20,0]]]
        import datetime
        for item in gData:
            key = item[0]#+'##'+item[1]
            #print key
            if service_info.has_key(key): # and service_info.get(key).keys() == 'OK' or 'WARNING':
                if item[1] == 'OK':
                    sec1 = int(datetime.timedelta(hours=item[3][0],minutes=item[3][1],seconds=item[3][2]).total_seconds()) - int(datetime.timedelta(hours=item[2][0],minutes=item[2][1],seconds=item[2][2]).total_seconds())
                    if service_info[key].has_key('OK'):
                        t1 = service_info[key]['OK'] + sec1
                        service_info[key]['OK'] = t1
                    else:
                        service_info[key].update({'OK':sec1})

                elif item[1] == 'WARNING':
                    sec1 = int(datetime.timedelta(hours=item[3][0],minutes=item[3][1],seconds=item[3][2]).total_seconds()) - int(datetime.timedelta(hours=item[2][0],minutes=item[2][1],seconds=item[2][2]).total_seconds())
                    if service_info[key].has_key('WARNING'):
                        t1 = service_info[key]['WARNING'] + sec1
                        service_info[key]['WARNING'] = t1
                    else:
                        service_info[key].update({'WARNING':sec1})

                elif item[1] == 'CRITICAL':
                    sec1 = int(datetime.timedelta(hours=item[3][0],minutes=item[3][1],seconds=item[3][2]).total_seconds()) - int(datetime.timedelta(hours=item[2][0],minutes=item[2][1],seconds=item[2][2]).total_seconds())
                    if service_info[key].has_key('CRITICAL'):
                        t1 = service_info[key]['CRITICAL'] + sec1
                        service_info[key]['CRITICAL'] = t1
                    else:
                        service_info[key].update({'CRITICAL':sec1})

            else:
                if item[1] == 'OK':
                    sec2 = int(datetime.timedelta(hours=item[3][0],minutes=item[3][1],seconds=item[3][2]).total_seconds()) - int(datetime.timedelta(hours=item[2][0],minutes=item[2][1],seconds=item[2][2]).total_seconds())
                    service_info.update({key:{'OK':sec2}})
                elif item[1] == 'WARNING':
                    sec2 = int(datetime.timedelta(hours=item[3][0],minutes=item[3][1],seconds=item[3][2]).total_seconds()) - int(datetime.timedelta(hours=item[2][0],minutes=item[2][1],seconds=item[2][2]).total_seconds())
                    service_info.update({key:{'WARNING':sec2}})
                elif item[1] == 'CRITICAL':
                    sec2 = int(datetime.timedelta(hours=item[3][0],minutes=item[3][1],seconds=item[3][2]).total_seconds()) - int(datetime.timedelta(hours=item[2][0],minutes=item[2][1],seconds=item[2][2]).total_seconds())
                    service_info.update({key:{'CRITICAL':sec2}})

        #find percentage and write into file for archive chart
        startTime = map(int,self.stime.split(' ')[1].split(':'))
        total_seconds = int(datetime.timedelta(hours=endTime[0],minutes=endTime[1],seconds=endTime[2]).total_seconds()) - int(datetime.timedelta(hours=startTime[0],minutes=startTime[1],seconds=startTime[2]).total_seconds())
        #print total_seconds
        for key,value in service_info.iteritems():
            for i in value.keys():
                service_info[key][i] = (value.get(i)*100/total_seconds)#round((value.get(i)*100/total_seconds),2)

        #print service_info
        f = open(archivefile,'w+')
        for key in service_info.keys():
            # hostname,service_name = key.split(' - ')
            service_name,hostname = key.split(' - ')
            f.write("%s,%s,%s,%s\n"%(hostname,service_name,service_info[key].get('OK',0),service_info[key].get('CRITICAL',0)))
        f.close()


           
    
    def getArchiveData(self,fileName):
        try:
            fp = open(fileName)
        except IOError as e:
            print "Error while opening the file %s...%s" % (fileName,e)
            return
        lines = fp.readlines()
        for line in lines:
            rec = line.rstrip("\n").split(",")
            #print rec
            serviceHost = rec[0]
            serviceName = rec[1]
            # desc = rec[1]
            data = [int(rec[2]),int(rec[3])] #rec[2:] # [ok,critical]
            #print data
            gData = graphData(serviceName,serviceHost,data=data)
            if self.gDataDict.has_key(rec[0]+'##'+rec[1]):
                gDataList = self.gDataDict[rec[0]+'##'+rec[1]]
                gDataList.append(gData)
            else:
                gDataList = []
                gDataList.append(gData)
                self.gDataDict[rec[0]+'##'+rec[1]] = gDataList


        # data_retriever.printgDataDict(self.gDataDict)


    @staticmethod    
    def printgDataDict(gDataDict):
        for dkey in gDataDict:
            serviceList = gDataDict.get(dkey)
            #print serviceList
            for gData in serviceList:
                print "%s,%s,%s,%s,%s" % (gData.getServiceName(), gData.getHostName(),
                                          gData.getDesc(),gData.getStatus(),gData.getTS())
    
if __name__ == '__main__':
    dr = data_retriever()
    dr.caculateServiceStatePercent("/tmp/nrecord")
    
    #dr.getArchiveData('/home/openstack/Desktop/archive')
    #gdata = dr.getDataDict()
    #print dir(gdata)
    #print gdata

    
                
                
            
            
            
        

