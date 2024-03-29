from constants import CONTRACT, NUM_RECORDS_HISTORY
from datetime import datetime
from web3 import Web3
import time
import json


# Save historical trade information to use in training
def save_history():
    current_epoch = CONTRACT.functions.currentEpoch().call()
    check_epoch = current_epoch - NUM_RECORDS_HISTORY

    # Initialize
    records = []

    # Store record for each epoch
    while check_epoch < current_epoch:
        try:
            current_rounds_list = CONTRACT.functions.rounds(check_epoch).call()
        except Exception as e:
            print("An error occurred at epoch: ", check_epoch)
            print(e)
            return

        lock_timestamp, lock_price, close_price, _, _, total_amount, bull_amount, bear_amount, *_ = current_rounds_list

        # Sleep (optional, can be removed or adjusted as needed)
        time.sleep(0.2)

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
            "epoch": check_epoch,
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

        # Add to records
        records.append(item_dict)

        # Increment by 1
        check_epoch += 1

    # Save the records to the 'history.json' file
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=4)
