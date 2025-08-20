# Install required packages
# pip install numpy pandas matplotlib scikit-learn tensorflow

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

# -----------------------------
# Step 1: Load data
# -----------------------------
DATA_FILE = 'sales_data.csv'  # CSV with 'date' and 'sales' columns
data = pd.read_csv(DATA_FILE, parse_dates=['date']).sort_values('date')

# Optional: add more features for better prediction
# For example: day of week, month, holiday flag
data['day_of_week'] = data['date'].dt.dayofweek
data['month'] = data['date'].dt.month

# Features and target
features = ['sales', 'day_of_week', 'month']
target = 'sales'

X_raw = data[features].values
y_raw = data[target].values.reshape(-1,1)

# -----------------------------
# Step 2: Scale data
# -----------------------------
scaler_X = MinMaxScaler()
scaler_y = MinMaxScaler()

X_scaled = scaler_X.fit_transform(X_raw)
y_scaled = scaler_y.fit_transform(y_raw)

# -----------------------------
# Step 3: Create sequences
# -----------------------------
SEQ_LENGTH = 30  # past 30 days
def create_sequences_multi(X, y, seq_length):
    X_seq, y_seq = [], []
    for i in range(len(X) - seq_length):
        X_seq.append(X[i:i+seq_length])
        y_seq.append(y[i+seq_length])
    return np.array(X_seq), np.array(y_seq)

X_seq, y_seq = create_sequences_multi(X_scaled, y_scaled, SEQ_LENGTH)

# Reshape for LSTM [samples, timesteps, features]
X_seq = X_seq.reshape(X_seq.shape[0], X_seq.shape[1], len(features))

# -----------------------------
# Step 4: Build LSTM Model
# -----------------------------
model = Sequential()
model.add(LSTM(128, activation='relu', return_sequences=True, input_shape=(SEQ_LENGTH, len(features))))
model.add(Dropout(0.2))
model.add(LSTM(64, activation='relu'))
model.add(Dropout(0.2))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mse')

# -----------------------------
# Step 5: Train the model
# -----------------------------
model.fit(X_seq, y_seq, epochs=100, batch_size=16, verbose=1)

# -----------------------------
# Step 6: Predict next N days
# -----------------------------
N_DAYS = 7
last_seq = X_scaled[-SEQ_LENGTH:].reshape(1, SEQ_LENGTH, len(features))
future_preds = []

for _ in range(N_DAYS):
    pred = model.predict(last_seq)
    future_preds.append(pred[0][0])
    
    # Update last_seq by appending prediction and removing oldest day
    next_input = last_seq[0,1:,:].tolist()  # remove first day
    next_features = [pred[0][0], (data['date'].iloc[-1].dayofweek+1)%7, data['date'].iloc[-1].month]
    next_input.append(next_features)
    last_seq = np.array(next_input).reshape(1, SEQ_LENGTH, len(features))

# Inverse scale predictions
future_preds = scaler_y.inverse_transform(np.array(future_preds).reshape(-1,1))

# -----------------------------
# Step 7: Display results
# -----------------------------
future_dates = pd.date_range(start=data['date'].iloc[-1]+pd.Timedelta(days=1), periods=N_DAYS)
plt.figure(figsize=(12,6))
plt.plot(data['date'], data['sales'], label='Actual Sales')
plt.plot(future_dates, future_preds, marker='o', linestyle='--', color='red', label='Future Predictions')
plt.xlabel('Date')
plt.ylabel('Sales')
plt.title('Advanced Future Prediction Model')
plt.legend()
plt.show()

print("Predicted sales for next 7 days:")
for i, val in enumerate(future_preds, 1):
    print(f"Day {i}: {val[0]:.2f}")
