from func_write import send_tx
from func_xgboost import xgb_predict_ratio, xgb_predict_direction
from constants import CONTRACT, IS_EXECUTE_TRADE, w3, ACCOUNT_ADDRESS
from web3 import Web3
from datetime import datetime
import pandas as pd


# Make predictions
def make_predictions():
    # Get balance
    wallet_balance = w3.eth.getBalance(ACCOUNT_ADDRESS)
    human_balance = Web3.fromWei(wallet_balance, "ether")

    # Guard: Ensure minimum funds available (BNB)
    if human_balance < 0.5:
        return

    # Get current epoch
    current_epoch = CONTRACT.functions.currentEpoch().call()
    stats_epoch = current_epoch - 1
    try:
        current_rounds_list = CONTRACT.functions.rounds(stats_epoch).call()
    except Exception as e:
        print(f"An error occurred at epoch {stats_epoch}:")
        print(e)
        return

    # Extract information
    lock_timestamp, lock_price, close_price, _, _, total_amount, bull_amount, bear_amount, *_ = current_rounds_list

    # Convert datetime
    date_log = datetime.fromtimestamp(lock_timestamp)

    # Calculate Ratios
    total_amount_normal = round(float(Web3.fromWei(total_amount, "ether")), 5)
    bull_amount_normal = round(float(Web3.fromWei(bull_amount, "ether")), 5)
    bear_amount_normal = round(float(Web3.fromWei(bear_amount, "ether")), 5)

    # Ratios
    if bull_amount_normal != 0 and bear_amount_normal != 0:
        bull_ratio = round(bull_amount_normal / bear_amount_normal, 2) + 1
        bear_ratio = round(bear_amount_normal / bull_amount_normal, 2) + 1

        # Format numbers
        bull_ratio = float(f"{bull_ratio:.{3}g}")
        bear_ratio = float(f"{bear_ratio:.{3}g}")
    else:
        bull_ratio = 0
        bear_ratio = 0

    # Construct item
    item_dict = {
        "epoch": stats_epoch,
        "datetime": date_log.strftime('%Y-%m-%d %H:%M:%S'),
        "hour": date_log.hour,
        "minute": date_log.minute,
        "second": date_log.second,
        "lock_price": lock_price,
        "close_price": close_price,
        "total_amount": total_amount_normal,
        "bull_amount": bull_amount_normal,
        "bear_amount": bear_amount_normal,
        "bull_ratio": bull_ratio,
        "bear_ratio": bear_ratio,
    }

    # Construct DataFrame
    df = pd.DataFrame([item_dict])

    # Get predictions for payout ratio
    ratio_bull_pred, ratio_bull_pred_proba = xgb_predict_ratio(df)
    print("Bull Ratio Pred: ", ratio_bull_pred, ratio_bull_pred_proba)

    # Predict the direction as well
    df_2 = df.copy()
    direction_up_pred, direction_up_pred_proba = xgb_predict_direction(df_2)
    print("Direction Pred: ", direction_up_pred, direction_up_pred_proba)

    # Execute trades based on the predicted payout ratio (optional)
    if IS_EXECUTE_TRADE:
        if ratio_bull_pred == 1:
            send_tx("bear")
        else:
            send_tx("bull")
