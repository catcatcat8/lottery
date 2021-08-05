#!/usr/bin/python3
import brownie
import pytest

def test_valid_deposit(lottery, accounts):
    ether_deposit = 10**18
    tokens = ether_deposit // 10**16

    accounts[0].transfer(lottery, ether_deposit)

    assert lottery.balanceOf(accounts[0]) == tokens


def test_not_valid_deposit(lottery, accounts):
    ether_deposit = 10**15

    with brownie.reverts():
        accounts[0].transfer(lottery, ether_deposit)


def test_sender_balance_decreases(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    sender_balance = lottery.balanceOf(accounts[0])
    amount = sender_balance // 4

    lottery.transfer(accounts[1], amount, {'from': accounts[0]})

    assert lottery.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    receiver_balance = lottery.balanceOf(accounts[1])
    amount = lottery.balanceOf(accounts[0]) // 4

    lottery.transfer(accounts[1], amount, {'from': accounts[0]})

    assert lottery.balanceOf(accounts[1]) == receiver_balance + amount


def test_total_supply_not_affected(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    total_supply = lottery.totalSupply()
    amount = lottery.balanceOf(accounts[0])

    lottery.transfer(accounts[1], amount, {'from': accounts[0]})

    assert lottery.totalSupply() == total_supply


def test_returns_true(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    amount = lottery.balanceOf(accounts[0])
    tx = lottery.transfer(accounts[1], amount, {'from': accounts[0]})

    assert tx.return_value is True


def test_transfer_full_balance(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    amount = lottery.balanceOf(accounts[0])
    receiver_balance = lottery.balanceOf(accounts[1])

    lottery.transfer(accounts[1], amount, {'from': accounts[0]})

    assert lottery.balanceOf(accounts[0]) == 0
    assert lottery.balanceOf(accounts[1]) == receiver_balance + amount


def test_transfer_zero_tokens(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    sender_balance = lottery.balanceOf(accounts[0])
    receiver_balance = lottery.balanceOf(accounts[1])

    lottery.transfer(accounts[1], 0, {'from': accounts[0]})

    assert lottery.balanceOf(accounts[0]) == sender_balance
    assert lottery.balanceOf(accounts[1]) == receiver_balance


def test_transfer_to_self(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    sender_balance = lottery.balanceOf(accounts[0])
    amount = sender_balance // 4

    lottery.transfer(accounts[0], amount, {'from': accounts[0]})

    assert lottery.balanceOf(accounts[0]) == sender_balance


def test_insufficient_balance(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    balance = lottery.balanceOf(accounts[0])

    with brownie.reverts():
        lottery.transfer(accounts[1], balance + 1, {'from': accounts[0]})


def test_transfer_event_fires(lottery, accounts):
    ether_deposit = 10**18
    accounts[0].transfer(lottery, ether_deposit)

    amount = lottery.balanceOf(accounts[0])
    tx = lottery.transfer(accounts[1], amount, {'from': accounts[0]})

    assert len(tx.events) == 2
    assert tx.events["Transfer"].values() == [accounts[0], accounts[1], amount]