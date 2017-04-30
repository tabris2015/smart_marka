import numpy
import matplotlib.pyplot as plt
import pandas
import math
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

import argparse
import time
def create_dataset(dataset, look_back = 1):
    		dataX, dataY = [], []
		for i in range(len(dataset)-look_back-1):
			a = dataset[i:(i+look_back),0]
			dataX.append(a)
			dataY.append(dataset[i+look_back,0])
		return numpy.array(dataX), numpy.array(dataY)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=' RNN trainer')
	#parser.add_argument('-online', action='store_true',help='send request to server, default is false')
	parser.add_argument('-dataset', action='store', type=str, help='dataset for training')
	parser.add_argument('-epoch', action='store', type=int, help='training epochs')
	parser.add_argument('-batch', action='store', type=int, help='batch size')
	parser.add_argument('-loop', action='store', type=int, help='loopback')
	
	#parser.add_argument('-asarray', action='store_true',help='send data as array')
	args = parser.parse_args()
	file = args.dataset
	EPOCH = args.epoch
	BATCH_SIZE = args.batch
	LOOP_BACK = args.loop
	# convert an array of values into a dataset matrix
	
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
	look_back = LOOP_BACK
	trainX, trainY = create_dataset(train, look_back)
	testX, testY = create_dataset(test, look_back)
	print str(trainX.shape) + ',' + str(trainY.shape)

	#m=10
	#for i in range(len(trainX)):
	#	if m>i:
	#		print trainX[i]
	#		print trainY[i]

	# reshape input to be [samples, time steps, features]
	trainX = numpy.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
	testX = numpy.reshape(testX, (testX.shape[0], 1, testX.shape[1]))
	print str(trainX.shape) + ',' + str(trainY.shape)

	# create and fit the LSTM network
	model = Sequential()
	model.add(LSTM(4, input_shape=(1, look_back)))
	model.add(Dense(1))
	model.compile(loss='mean_squared_error', optimizer='adam')
	model.fit(trainX, trainY, epochs=EPOCH, batch_size=BATCH_SIZE, verbose=2)

	# model to JSON
	model_json = model.to_json()
	with open(file + '_model.json', 'w') as json_file:
		json_file.write(model_json)

	# serialize weights to HDF5
	model.save_weights(file + '_model.h5')
	print ('Saved model to disk')

