import json, time, math, statistics  
from boltiot import Sms, Bolt
#importing configuration file which holds the confidential data 
import conf   

#function to compute bounds or Z Score Analysis

def compute_bounds(history_data,frame_size,factor):
    if len(history_data)<frame_size :
        return None

    if len(history_data)>frame_size :
        del history_data[0:len(history_data)-frame_size]
    Mn=statistics.mean(history_data)
    Variance=0
    for data in history_data :
        Variance += math.pow((data-Mn),2)
    Zn = factor * math.sqrt(Variance / frame_size)
    High_bound = history_data[frame_size-1]+Zn
    Low_bound = history_data[frame_size-1]-Zn
    return [High_bound,Low_bound] 

mybolt = Bolt(conf.API_KEY, conf.DEVICE_ID)  #returns object of Bolt to mybolt and connects with the bolt device 
sms = Sms(conf.SSID, conf.AUTH_TOKEN, conf.TO_NUMBER, conf.FROM_NUMBER) #create a platform for the mobile networks and server to connect with each other
history_data=[] #list of the sensor values to be stored in

while True:
    response = mybolt.analogRead('A0') #reads the data from A0 pin
    data = json.loads(response) #converts the data in the python dictionary type
    if data['success'] != 1:
        print("There was an error while retriving the data.")
        print("This is the error:"+data['value'])
        time.sleep(10)
        continue

    print ("This is the value "+data['value'])
    sensor_value=0
    try:
        sensor_value = int(data['value'])
    except e:
        print("There was an error while parsing the response: ",e)
        continue

    try: 
        sensor_value = int(data['value'])
        minimum_limit = 341
        
        #alerts when the temperature goes below minimum limit-
        
        if sensor_value < minimum_limit: 
            print("Making request to Twilio to send a SMS")
            Temperature=(100*sensor_value)/1024 
            response = sms.send_sms("The Current temperature sensor value is " +str(sensor_value)+"and in celcius" +str(Temperature))
            print("Response received from Twilio is: " + str(response))
            print("Status of SMS at Twilio is :" + str(response.status))
    except Exception as e: 
        print ("Error occured: Below are the details")
        print (e)

    bound = compute_bounds(history_data,conf.FRAME_SIZE,conf.MUL_FACTOR) #calls the function and as a result it returns low and high bound 
    if not bound: #if the function returns none 
        required_data_count=conf.FRAME_SIZE-len(history_data) 
        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
        history_data.append(int(data['value']))
        time.sleep(10)
        continue
    
        #alerts when there is a sudden raise or drop in temperature-
    
    try:
        if sensor_value > bound[0] : #if value greater than high bound
            print ("The Temperature level increased suddenly. Sending an SMS.")
            response = sms.send_sms("Someone switched on the I-heat mode in Heater")
            print("This is the response ",response)
        elif sensor_value < bound[1]: #if value lower than low bound
            print ("The Temperature level decreased suddenly. Sending an SMS.")
            response = sms.send_sms("Someone switched on the I-cool mode in AC")
            print("This is the response ",response)
        history_data.append(sensor_value);
    except Exception as e:
        print ("Error",e)

    
    
    time.sleep(10)
