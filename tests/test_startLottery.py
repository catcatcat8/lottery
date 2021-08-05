#!/usr/bin/python3
import brownie

def test_valid_start_first_lottery(lottery, accounts, chain):
    lottery_id = 0
    status = "PurchaseTickets"
    start_time = chain.time()
    close_time = 0
    init_prize_pool = 0
    winner = "0x0000000000000000000000000000000000000000"

    lottery.startLottery({'from': accounts[0]})

    assert lottery.allLotteries(lottery_id + 1)[0] == lottery_id + 1  # increment lottery_id
    assert lottery.getCurrentLotteryStatus() == status
    assert lottery.allLotteries(lottery_id + 1)[2] in range(start_time, start_time + 2)  # operations from above will take no more than a second
    assert lottery.allLotteries(lottery_id + 1)[3] == close_time
    assert lottery.allLotteries(lottery_id + 1)[4] == init_prize_pool
    assert lottery.allLotteries(lottery_id + 1)[5] == winner


def test_start_lottery_from_non_contract_owner(lottery, accounts):
    with brownie.reverts():
        lottery.startLottery({'from': accounts[1]})


def test_two_starts_lottery(lottery, accounts):
    lottery.startLottery({'from': accounts[0]})

    with brownie.reverts():
        lottery.startLottery({'from': accounts[0]})


def test_start_lottery_after_it_was_closed_but_not_completed(lottery, accounts, chain):
    accounts[1].transfer(lottery, 10**18)
    accounts[2].transfer(lottery, 10**18)

    lottery.startLottery({'from': accounts[0]})

    lottery.buyTickets(10, {'from': accounts[1]})
    lottery.buyTickets(10, {'from': accounts[2]})

    chain.sleep(3601)  # 1 hour and 1 second (more than 1 hour)
    lottery.closePurchaseStage({'from': accounts[0]})

    assert (lottery.getCurrentLotteryStatus() == "Closed")

    with brownie.reverts():
        lottery.startLottery({'from': accounts[0]})


def test_valid_start_next_lottery_after_it_was_completed(lottery, accounts, chain):
    accounts[1].transfer(lottery, 10**18)
    accounts[2].transfer(lottery, 10**18)

    lottery.startLottery({'from': accounts[0]})

    lottery_id = 1

    lottery.buyTickets(10, {'from': accounts[1]})
    lottery.buyTickets(10, {'from': accounts[2]})

    chain.sleep(3601)  # 1 hour and 1 second (more than 1 hour)
    lottery.closePurchaseStage({'from': accounts[0]})

    assert (lottery.getCurrentLotteryStatus() == "Closed")

    lottery.completeLottery({'from': accounts[0]})

    status = "PurchaseTickets"
    start_time = chain.time()
    close_time = 0
    init_prize_pool = 0
    winner = "0x0000000000000000000000000000000000000000"

    lottery.startLottery({'from': accounts[0]})

    assert lottery.allLotteries(lottery_id + 1)[0] == lottery_id + 1  # increment lottery_id
    assert lottery.getCurrentLotteryStatus() == status
    assert lottery.allLotteries(lottery_id + 1)[2] in range(start_time, start_time + 2)  # operations from above will take no more than a second
    assert lottery.allLotteries(lottery_id + 1)[3] == close_time
    assert lottery.allLotteries(lottery_id + 1)[4] == init_prize_pool
    assert lottery.allLotteries(lottery_id + 1)[5] == winner


def test_start_lottery_event_fires(lottery, accounts):
    lottery_id = 0
    tx = lottery.startLottery({'from': accounts[0]})

    assert len(tx.events) == 1
    assert tx.events["OpeningLottery"].values() == [lottery_id + 1]
