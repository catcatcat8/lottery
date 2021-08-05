#!/usr/bin/python3
import brownie


def test_sender_balance_decreases(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    sender_balance = lottery.balanceOf(accounts[0])
    amount = sender_balance // 4

    lottery.approve(accounts[1], amount, {'from': accounts[0]})
    lottery.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert lottery.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    receiver_balance = lottery.balanceOf(accounts[2])
    amount = lottery.balanceOf(accounts[0]) // 4

    lottery.approve(accounts[1], amount, {'from': accounts[0]})
    lottery.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert lottery.balanceOf(accounts[2]) == receiver_balance + amount


def test_caller_balance_not_affected(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    caller_balance = lottery.balanceOf(accounts[1])
    amount = lottery.balanceOf(accounts[0])

    lottery.approve(accounts[1], amount, {'from': accounts[0]})
    lottery.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert lottery.balanceOf(accounts[1]) == caller_balance


def test_caller_approval_affected(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    approval_amount = lottery.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    lottery.approve(accounts[1], approval_amount, {'from': accounts[0]})
    lottery.transferFrom(accounts[0], accounts[2], transfer_amount, {'from': accounts[1]})

    assert lottery.allowance(accounts[0], accounts[1]) == approval_amount - transfer_amount


def test_receiver_approval_not_affected(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    approval_amount = lottery.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    lottery.approve(accounts[1], approval_amount, {'from': accounts[0]})
    lottery.approve(accounts[2], approval_amount, {'from': accounts[0]})
    lottery.transferFrom(accounts[0], accounts[2], transfer_amount, {'from': accounts[1]})

    assert lottery.allowance(accounts[0], accounts[2]) == approval_amount


def test_total_supply_not_affected(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    total_supply = lottery.totalSupply()
    amount = lottery.balanceOf(accounts[0])

    lottery.approve(accounts[1], amount, {'from': accounts[0]})
    lottery.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert lottery.totalSupply() == total_supply


def test_returns_true(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    amount = lottery.balanceOf(accounts[0])
    lottery.approve(accounts[1], amount, {'from': accounts[0]})
    tx = lottery.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert tx.return_value is True


def test_transfer_full_balance(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    amount = lottery.balanceOf(accounts[0])
    receiver_balance = lottery.balanceOf(accounts[2])

    lottery.approve(accounts[1], amount, {'from': accounts[0]})
    lottery.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert lottery.balanceOf(accounts[0]) == 0
    assert lottery.balanceOf(accounts[2]) == receiver_balance + amount


def test_transfer_zero_lotterys(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    sender_balance = lottery.balanceOf(accounts[0])
    receiver_balance = lottery.balanceOf(accounts[2])

    lottery.approve(accounts[1], sender_balance, {'from': accounts[0]})
    lottery.transferFrom(accounts[0], accounts[2], 0, {'from': accounts[1]})

    assert lottery.balanceOf(accounts[0]) == sender_balance
    assert lottery.balanceOf(accounts[2]) == receiver_balance


def test_transfer_zero_lotterys_without_approval(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    sender_balance = lottery.balanceOf(accounts[0])
    receiver_balance = lottery.balanceOf(accounts[2])

    lottery.transferFrom(accounts[0], accounts[2], 0, {'from': accounts[1]})

    assert lottery.balanceOf(accounts[0]) == sender_balance
    assert lottery.balanceOf(accounts[2]) == receiver_balance


def test_insufficient_balance(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    balance = lottery.balanceOf(accounts[0])

    lottery.approve(accounts[1], balance + 1, {'from': accounts[0]})
    with brownie.reverts():
        lottery.transferFrom(accounts[0], accounts[2], balance + 1, {'from': accounts[1]})


def test_insufficient_approval(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    balance = lottery.balanceOf(accounts[0])

    lottery.approve(accounts[1], balance - 1, {'from': accounts[0]})
    with brownie.reverts():
        lottery.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_no_approval(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    balance = lottery.balanceOf(accounts[0])

    with brownie.reverts():
        lottery.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_revoked_approval(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    balance = lottery.balanceOf(accounts[0])

    lottery.approve(accounts[1], balance, {'from': accounts[0]})
    lottery.approve(accounts[1], 0, {'from': accounts[0]})

    with brownie.reverts():
        lottery.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_transfer_to_self(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    sender_balance = lottery.balanceOf(accounts[0])
    amount = sender_balance // 4

    lottery.approve(accounts[0], sender_balance, {'from': accounts[0]})
    lottery.transferFrom(accounts[0], accounts[0], amount, {'from': accounts[0]})

    assert lottery.balanceOf(accounts[0]) == sender_balance
    assert lottery.allowance(accounts[0], accounts[0]) == sender_balance - amount


def test_transfer_to_self_no_approval(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    amount = lottery.balanceOf(accounts[0])

    with brownie.reverts():
        lottery.transferFrom(accounts[0], accounts[0], amount, {'from': accounts[0]})


def test_transfer_event_fires(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    amount = lottery.balanceOf(accounts[0])

    tx = lottery.approve(accounts[1], amount, {'from': accounts[0]})
    assert tx.events["Approval"].values() == [accounts[0], accounts[1], amount]

    tx = lottery.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})
    assert len(tx.events) == 3
    assert tx.events["Transfer"].values() == [accounts[0], accounts[2], amount]