from flask import Flask, render_template, request, jsonify
from DataRetriever import data_retriever
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

#@app.route('/status')
#def status():
#    return "Status"

#@app.route('/graph')
#def chart():
#    return render_template('chart.html')

@app.route('/timeline')
def timeline():
    print "Time line"
    return render_template('timeline.html')

@app.route('/archive')
def archive():
    print "archive data"
    return render_template('archive.html')


@app.route('/archivedata')
def archivedata():
    print "Time line"
    # return render_template('archive.html')
    gData = [['Services', 'OK', 'CRITICAL']]
    dr = data_retriever()
    dr.getArchiveData("/tmp/archive1")
    gDataDict = dr.getDataDict()
    print gDataDict
    # gdata = []
    for k in gDataDict.keys():
        servicename = k.split('##')[1]
        for item in gDataDict.get(k):
            temp = []
            print item.getServiceName()
            print item.getData()
            temp.append(item.getServiceName())
            temp.extend(item.getData())
            print temp
        gData.append(temp)
    print gData

    # gdata = [['Services', 'OK', 'CRITICAL'],['Service-1', 60, 40],['Service-2', 80, 20,],['Service-3', 70, 30]]
    return str(gData)

@app.route('/tldata')
def timelinedata():
    dr = data_retriever()
    dr.getTimeLineData("/tmp/nrecord")
    dr1 = data_retriever()
    dr1.caculateServiceStatePercent("/tmp/nrecord")
    gDataDict = dr.getDataDict()
    gDataDict = dr.getDataDict()
    gData = []
    endTime = map(int,dr.getETime().split(' ')[1].split(':'))
    
    print endTime
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
    print gData    


    #gData = [['NS','OK',[14,0,0],[14,15,0]],['NS','CRITICAL',[14,15,0],[14,20,0]]]
    """
    TestStartDate:2015-05-05 15:00:00
    Service-1##Host-1,2015-05-05 15:01:01,WARNING,Nova Failure
    Service-1##Host-1,2015-05-05 15:02:01,OK,Nova Works
    Service-2##Host-1,2015-05-05 15:01:01,WARNING,Neutron Failure
    Service-2##Host-1,2015-05-05 15:03:01,OK,Neutron Failure
    TestEndDate:2015-05-05 16:00:00
    """
    #gData = [['Service-1##Host-1','WARNING',[15,1,1],[15,02,01]],['NS','OK',[15,02,01],[16,0,0]],
    #          ['Service-2##Host-1','WARNING',[15,1,1],[15,3,1]],['NS','OK',[15,3,1],[16,0,0]],
    #		]
    return str(gData)

#@app.route('/barchart')
#def barchart():
#    return render_template('barchart.html')

#@app.route('/stackbarchart')
#def stackbarchart():
#    return render_template('stackbarchart.html')

@app.route('/_add_numbers')
def add_numbers():
    a = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)
    print str(jsonify(result=a + b))
    return jsonify(result=a + b)

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int("8090"),
        debug=True
    )


