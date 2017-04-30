import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM

scaler = MinMaxScaler(feature_range=(-1, 1))


df = pd.read_csv("rainfallbolivia.csv")
mm = df['mm_per_day'].values
mm = mm.reshape(len(mm), 1)
scaler = scaler.fit(mm)

scaled_mm = scaler.transform(mm)


days_to_predict = 60
train, test = scaled_mm[0:-days_to_predict], scaled_mm[-days_to_predict:]

print ('train: ', train.shape)
print ('test: ', test.shape)

# frame a sequence as a supervised learning problem
def timeseries_to_supervised(data, lag=1):
    df = pd.DataFrame(data)
    columns = [df.shift(i) for i in range(1, lag+1)]
    columns.append(df)
    df = pd.concat(columns, axis=1)
    df.fillna(0, inplace=True)
    df.columns = ['X', 'y']
    return df

train_df = timeseries_to_supervised(train, 1)
test_df = timeseries_to_supervised(test, 1)

print(train_df.head())

print train_df.shape
X_train, y_train = train_df.X.values, train_df.y.values
X_test, y_test = test_df.X.values, test_df.y.values



print X_train.shape, y_train.shape
X_train = X_train.reshape(X_train.shape[0], 1, 1)
y_train = y_train.reshape(y_train.shape[0], 1)

X_test = X_test.reshape(X_test.shape[0], 1, 1)
y_test = y_test.reshape(y_test.shape[0], 1)

print (X_train.shape, y_train.shape)


####keras
#### hiper parameters
BATCH_SIZE = 37
UNITS = 64
EPOCH = 100
model = Sequential()

model.add(LSTM(UNITS, batch_input_shape=(BATCH_SIZE, X_train.shape[1], X_train.shape[2]), stateful=True))
model.add(Dense(1))
model.compile(loss='mean_squared_error', optimizer='adam')

model.fit(X_train, y_train, epochs=EPOCH, batch_size=BATCH_SIZE, verbose=1, shuffle=False)
model.evaluate(X_test, y_test, batch_size=BATCH_SIZE)
# model.reset_states()

