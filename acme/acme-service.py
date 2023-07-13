from xmlrpc.server import SimpleXMLRPCServer
import paho.mqtt.client as mqtt
import multiprocessing
import json

broker_address = '192.168.1.100'
port = 1883
timeout = 60
username = 'admin'
password = 'admin'
relay_sn = 'JM1586FC7DEB51ED'


def get_poweroncmd_unmatched(sn, io):
    poweron_cmd={
        'id':'2028106',
        'sn':sn,
        'params':[
            {
            'p':'COM_ALL',
            'k':'mb',
            'v':{
                'opr':'openone',
                'io':io,
                'time':10,
                'addr':254
                }
            }
        ]
    }
    return poweron_cmd

def get_poweroffcmd_unmatched(sn, io):
    poweroff_cmd={
        "id":"2028106",
        "sn":sn,
        "params":[
            {
            "p":"COM_ALL",
            "k":"mb",
            "v":{
                "opr":'openone',
                "io":io,
                "time":30,
                "addr":254
                }
            }
        ]
    }
    return poweroff_cmd

def get_poweroncmd_visionfive(sn, io):
    poweron_cmd={
        'id':'2028106',
        'sn':sn,
        'params':[
            {
            'p':'COM_ALL',
            'k':'mb',
            'v':{
                'opr':'open',
                'io':io,
                'addr':254
                }
            }
        ]
    }
    return poweron_cmd

def get_poweroffcmd_visionfive(sn, io):
    poweroff_cmd={
        "id":"2028106",
        "sn":sn,
        "params":[
            {
            "p":"COM_ALL",
            "k":"mb",
            "v":{
                "opr":'close',
                "io":io,
                "addr":254
                }
            }
        ]
    }
    return poweroff_cmd

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    sub_topic = '/sys/plct/{}/pub'.format(relay_sn)
    print ('sub_topic>>>', sub_topic)
    client.subscribe(sub_topic)

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload) + '\n')
    
def on_disconnect(client, userdata, rc):
    print("Closing data file...")

def connect_mqtt():
    client = mqtt.Client()
    # print('00000',client)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.username_pw_set(username, password)
    client.connect(broker_address, port, 60)
    client.loop_start()
    # client.loop_forever()
    return client

class ServiceMethod(object):
    @staticmethod
    def switch_on(device,io):
        client = connect_mqtt()
        if device == 'unmatched':
          poweron_cmd = get_poweroncmd_unmatched(relay_sn, int(io))
        elif device == 'visionfive':
          poweron_cmd = get_poweroncmd_visionfive(relay_sn, int(io))
        else:
          return 'Invalid Device'
        poweron_cmd_new = json.dumps(poweron_cmd, separators=(',',':'))
        set_topic = '/sys/plct/{}/set'.format(relay_sn)
        result = client.publish(set_topic, poweron_cmd_new)
        print ('set_topic>>>', set_topic)
        print ('poweron_cmd>>>', poweron_cmd_new)
        print ('poweron_result>>>', result.rc)
        if result.rc == 0:
           return 'Switch_on Successfully'
        else:
           return 'Switch_on Unsuccessfully'
        
        
    @staticmethod
    def switch_off(device,io):
        client = connect_mqtt()
        if device == 'unmatched':
          poweroff_cmd = get_poweroffcmd_unmatched(relay_sn, int(io))
        elif device == 'visionfive':
          poweroff_cmd = get_poweroffcmd_visionfive(relay_sn, int(io))
        else:
          return 'Invalid Device'
        poweroff_cmd_new = json.dumps(poweroff_cmd, separators=(',',':'))
        set_topic = '/sys/plct/{}/set'.format(relay_sn)
        result = client.publish(set_topic, poweroff_cmd_new)
        print ('set_topic>>>', set_topic)
        print ('poweroff_cmd>>>', poweroff_cmd_new)
        print ('poweroff_result>>>', result.rc)
        if result.rc == 0:
           return 'Switch_off Successfully'
        else:
           return 'Switch_off Unsuccessfully'




def setup_socket_server(ip_address, port=6666):
    try:
        service = SimpleXMLRPCServer((ip_address, port))  # 初始化XML-RPC服务
        print('Server {} Listening on port {} ...'.format(ip_address, port))
        service.register_instance(ServiceMethod())  # 注册一个类
        service.serve_forever()  # 启动服务器并永久运行
    except Exception as ex:
        raise Exception('Setup socket server error:\n{}'.format(ex))



if __name__ == '__main__':
   setup_socket_server(ip_address='192.168.10.20')
