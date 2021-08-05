#!/usr/bin/python3
import brownie

def test_lottery_was_not_closed_yet(lottery, accounts):
    lottery.startLottery({'from': accounts[0]})
    assert (lottery.getCurrentLotteryStatus() != "Closed")

    with brownie.reverts():
        lottery.completeLottery({'from': accounts[0]})


def test_complete_by_non_contract_owner(lottery, accounts, chain):
    lottery.startLottery({'from': accounts[0]})

    accounts[1].transfer(lottery, 10**18)
    accounts[2].transfer(lottery, 10**18)

    lottery.buyTickets(10, {'from': accounts[1]})
    lottery.buyTickets(10, {'from': accounts[2]})

    chain.sleep(3601)  # 1 hour and 1 second (more than 1 hour)
    lottery.closePurchaseStage({'from': accounts[0]})

    with brownie.reverts():
        lottery.completeLottery({'from': accounts[1]})


def test_winner_balance_increases(lottery, accounts, chain):
    lottery.startLottery({'from': accounts[0]})

    accounts[1].transfer(lottery, 10**18)
    accounts[2].transfer(lottery, 10**18)

    lottery.buyTickets(10, {'from': accounts[1]})
    lottery.buyTickets(10, {'from': accounts[2]})
    prize_pool = lottery.getCurrentTotalPurchasedTickets()

    balance_of_winner_before_lottery_was_completed = lottery.balanceOf(accounts[1])  # or lottery.balanceOf(accounts[2]), it's equal

    chain.sleep(3601)  # 1 hour and 1 second (more than 1 hour)
    lottery.closePurchaseStage({'from': accounts[0]})
    lottery.completeLottery({'from': accounts[0]})

    winner = lottery.getWinnerOfLottery()
    
    assert lottery.balanceOf(winner) == balance_of_winner_before_lottery_was_completed + prize_pool - 1  # 1 token commission


def test_loser_balance_not_increases(lottery, accounts, chain):
    lottery.startLottery({'from': accounts[0]})

    accounts[1].transfer(lottery, 10**18)
    accounts[2].transfer(lottery, 10**18)

    lottery.buyTickets(10, {'from': accounts[1]})
    lottery.buyTickets(10, {'from': accounts[2]})

    balance_of_loser_before_lottery_was_completed = lottery.balanceOf(accounts[1])  # or lottery.balanceOf(accounts[2]), it's equal

    chain.sleep(3601)  # 1 hour and 1 second (more than 1 hour)
    lottery.closePurchaseStage({'from': accounts[0]})
    lottery.completeLottery({'from': accounts[0]})

    winner = lottery.getWinnerOfLottery()
    if (winner == accounts[1]):
        loser = accounts[2]
    else:
        loser = accounts[1]
    
    assert lottery.balanceOf(loser) == balance_of_loser_before_lottery_was_completed


def test_1_token_commission_to_contract_owner(lottery, accounts, chain):
    contract_owner = accounts[0]
    lottery.startLottery({'from': contract_owner})

    accounts[1].transfer(lottery, 10**18)
    accounts[2].transfer(lottery, 10**18)

    balance_of_contract_owner_before_lottery_was_completed = lottery.balanceOf(contract_owner)

    lottery.buyTickets(10, {'from': accounts[1]})
    lottery.buyTickets(10, {'from': accounts[2]})

    chain.sleep(3601)  # 1 hour and 1 second (more than 1 hour)
    lottery.closePurchaseStage({'from': contract_owner})
    lottery.completeLottery({'from': contract_owner})

    assert lottery.balanceOf(contract_owner) == balance_of_contract_owner_before_lottery_was_completed + 1


def test_complete_status(lottery, accounts, chain):
    lottery.startLottery({'from': accounts[0]})

    accounts[1].transfer(lottery, 10**18)
    accounts[2].transfer(lottery, 10**18)

    lottery.buyTickets(10, {'from': accounts[1]})
    lottery.buyTickets(10, {'from': accounts[2]})

    chain.sleep(3601)  # 1 hour and 1 second (more than 1 hour)
    lottery.closePurchaseStage({'from': accounts[0]})
    lottery.completeLottery({'from': accounts[0]})

    assert lottery.getCurrentLotteryStatus() == "Completed"


def test_complete_lottery_event_fires(lottery, accounts, chain):
    lottery_id = 0
    lottery.startLottery({'from': accounts[0]})

    accounts[1].transfer(lottery, 10**18)
    accounts[2].transfer(lottery, 10**18)

    lottery.buyTickets(10, {'from': accounts[1]})
    lottery.buyTickets(10, {'from': accounts[2]})

    chain.sleep(3601)  # 1 hour and 1 second (more than 1 hour)
    lottery.closePurchaseStage({'from': accounts[0]})
    tx = lottery.completeLottery({'from': accounts[0]})

    assert tx.events["CompletingLottery"].values() == [lottery_id + 1]