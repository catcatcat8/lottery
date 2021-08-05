#!/usr/bin/python3
import brownie

def test_lottery_has_not_started(lottery, accounts):
    assert (lottery.getCurrentLotteryStatus() == "NotStarted")

    with brownie.reverts():
        lottery.buyTickets(10, {'from': accounts[1]})


def test_buy_tickets_without_tokens(lottery, accounts):
    lottery.startLottery({'from': accounts[0]})

    assert (lottery.balanceOf(accounts[1]) == 0)

    with brownie.reverts():
        lottery.buyTickets(10, {'from': accounts[1]})


def test_insufficient_funds(lottery, accounts):
    lottery.startLottery({'from': accounts[0]})

    accounts[1].transfer(lottery, 10**18)
    balance = lottery.balanceOf(accounts[1])

    with brownie.reverts():
        lottery.buyTickets(balance + 1, {'from': accounts[1]})


def test_valid_buying_tickets(lottery, accounts):
    total_tickets_before_buying = 0

    lottery.startLottery({'from': accounts[0]})

    accounts[1].transfer(lottery, 10**18)
    balance_before_buying = lottery.balanceOf(accounts[1])
    desired_tickets_number = 5

    lottery.buyTickets(desired_tickets_number, {'from': accounts[1]})

    assert(lottery.getAmountOfTickets(accounts[1]) == desired_tickets_number)
    assert(lottery.balanceOf(accounts[1]) == balance_before_buying - desired_tickets_number)
    assert(lottery.getCurrentTotalPurchasedTickets() == total_tickets_before_buying + desired_tickets_number)


def test_buy_tickets_after_lottery_was_closed(lottery, accounts, chain):
    accounts[1].transfer(lottery, 10**18)
    accounts[2].transfer(lottery, 10**18)

    lottery.startLottery({'from': accounts[0]})

    lottery.buyTickets(10, {'from': accounts[1]})
    lottery.buyTickets(10, {'from': accounts[2]})

    chain.sleep(3601)  # 1 hour and 1 second (more than 1 hour)
    lottery.closePurchaseStage({'from': accounts[0]})

    assert (lottery.getCurrentLotteryStatus() == "Closed")

    with brownie.reverts():
        lottery.buyTickets(1, {'from': accounts[1]})


def test_buy_more_than_200_tickets(lottery, accounts):
    lottery.startLottery({'from': accounts[0]})

    desired_tokens_number = 201
    accounts[1].transfer(lottery, desired_tokens_number * 10**16)

    with brownie.reverts():
        lottery.buyTickets(desired_tokens_number, {'from': accounts[1]})


def test_buy_tickets_event_fires(lottery, accounts):
    lottery.startLottery({'from': accounts[0]})

    accounts[1].transfer(lottery, 10**18)
    desired_tickets_number = 5
    tx = lottery.buyTickets(desired_tickets_number, {'from': accounts[1]})

    assert len(tx.events) == 2
    assert tx.events["BurnTokens"].values() == [accounts[1], desired_tickets_number]
    assert tx.events["PurchasingTickets"].values() == [accounts[1], desired_tickets_number]
