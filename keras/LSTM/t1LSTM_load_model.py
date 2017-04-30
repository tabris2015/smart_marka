import numpy
import matplotlib.pyplot as plt
import pandas
import math
from keras.models import model_from_json
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error	

import argparse

import requests

import time

# convert an array of values into a dataset matrix
def create_dataset(dataset, look_back = 1):
	dataX, dataY = [], []
	for i in range(len(dataset)-look_back-1):
		a = dataset[i:(i+look_back),0]
		dataX.append(a)
		dataY.append(dataset[i+look_back,0])
	return numpy.array(dataX), numpy.array(dataY)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=' RNN trainer')
	parser.add_argument('-dataset', action='store', type=str, help='dataset for training')
	#parser.add_argument('-batch', action='store', type=int, help='training epochs')
	parser.add_argument('-loop', action='store', type=int, help='loopback')
	
	#parser.add_argument('-asarray', action='store_true',help='send data as array')
	args = parser.parse_args()
	# file of the dataset
	file = args.dataset
	LOOP_BACK = args.loop
	# fix random seed
	numpy.random.seed(7)

	# load dataset 'passengers.csv'
	dataframe = pandas.read_csv(file + '.csv', usecols=[1], engine = 'python', skipfooter = 3)
	dataset = dataframe.values
	print 'Dataset' + str(dataset.shape)
	#plt.plot(dataset)
	#plt.show()
	#m=100
	#for i in range(len(dataset)):
	#	if i < m:
	#		print dataset[i,:]
	dataset = dataset.astype('float32')

	# normalize the dataset
	scaler = MinMaxScaler(feature_range = (0,1))
	dataset = scaler.fit_transform(dataset)

	# split into train and test sets
	train_size = int(len(dataset)*0.67)
	test_size = len(dataset)-train_size
	train, test = dataset[0:train_size,:], dataset[train_size:len(dataset),:]
	print(len(train), len(test))

	# reshape into X=t and Y=t+1
	look_back =LOOP_BACK
	trainX, trainY = create_dataset(train, look_back)
	testX, testY = create_dataset(test, look_back)
	#print str(trainX.shape) + ',' + str(trainY.shape)
	trainX = numpy.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
	testX = numpy.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

	# load json and create model
	json_file = open(file + '_model.json', 'r')
	loaded_model_json = json_file.read()
	json_file.close()
	loaded_model = model_from_json(loaded_model_json)

	# load weights into new model
	loaded_model.load_weights(file + "_model.h5")
	print("Loaded model from disk")

	# evaluate loaded model on test data
	loaded_model.compile(loss='mean_squared_error', optimizer='adam')
	score = loaded_model.evaluate(testX, testY, verbose=2)
	trainPredict = loaded_model.predict(trainX)
	testPredict = loaded_model.predict(testX)

	# invert predictions
	testPredict = scaler.inverse_transform(testPredict)
	testY = scaler.inverse_transform([testY])

	# calculate root mean 
	testScore = math.sqrt(mean_squared_error(testY[0], testPredict[:,0]))
	print('Test Score: %.2f RMSE' % (testScore))

	# shift train predictions for plotting
	trainPredictPlot = numpy.empty_like(dataset)
	trainPredictPlot[:, :] = numpy.nan
	trainPredictPlot[look_back:len(trainPredict)+look_back, :] = trainPredict

	# shift test predictions for plotting
	testPredictPlot = numpy.empty_like(dataset)
	testPredictPlot[:, :] = numpy.nan
	#testPredictPlot[:, :] = 0
	testPredictPlot[len(trainPredict)+(look_back*2)+1:len(dataset)-1, :] = testPredict


	training_data = scaler.inverse_transform(dataset)
	training_data[- testPredict.shape[0]:] = numpy.nan
	"""
	testPredictPlot = testPredictPlot.flatten().tolist()


	training_data = scaler.inverse_transform(dataset).flatten().tolist()
	idx = numpy.arange(len(training_data)).tolist()

	training_data_list = []

	for i in idx:
    		training_data_list.append({i: training_data[i]})

	print training_data_list
	time.sleep(1)

	#print training_data.shape, testPredictPlot.shape
	# plot baseline and predictions
	print "enviando datos al server"
	url = 'http://ggizitim.enjambre.com.bo/storage/array/rnn' 
	#url = 'http://2af64eb1.ngrok.io/storage/array/rnn'
	print url
	time.sleep(1)
	request_header = {'Content-Type': 'application/json'}
	print "enviando train"
	key = file + '_train'
	train_dict = {'dataArray':training_data_list[10], 'name':key}
	r = requests.post(url,headers=request_header, json=train_dict)
	print r.status_code
	if r.status_code == requests.codes.ok:
    		logging.debug("enviado array de datos: " + key)
        
	time.sleep(2)


	predict_data_list = []

	for i in idx:
    		predict_data_list.append({i: predict_data[i]})

	print predict_data_list
	time.sleep(1)
	print "enviando predicciones"
	key = file + '_predict'
	predict_dict = {'dataArray':predict_data_list[10], 'name':key}
	r = requests.post(url,headers=request_header, json=predict_dict)
	print r.status_code
	if r.status_code == requests.codes.ok:
    		logging.debug("enviado array de datos: " + key)

	"""
	train_fig, train_ax = plt.subplots()
	train_ax.plot(training_data)
	train_ax.plot(testPredictPlot)
	train_ax.title()
	
	train_ax.grid(True)
	train_fig.savefig(file + '.png')
	#plt.plot(trainPredictPlot)
	
	#plt.show()

	#print("%s: %.2f%%" % (loaded_model.metrics_names[1], score[1]*100))
