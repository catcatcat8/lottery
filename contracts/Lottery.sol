// SPDX-License-Identifier: MIT

pragma solidity >0.6.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Lottery is IERC20, Ownable {
    using SafeMath for uint256;

    /// @notice EIP-20 token name for buying lottery tickets: 1 TLC = 0.01 ETH
    string public name = "TrueLotteryCoin";

    /// @notice EIP-20 token symbol for this token
    string public symbol = "TLC";

    /// @notice EIP-20 token decimals for this token
    uint8 public decimals = 18;

    /// @notice Total balances of tokens among the players
    uint256 public override totalSupply = 0;

    /// @notice One token ETH price
    uint256 public tokenPrice = 100;  // 1 Ether = 100 Tokens

    /// @notice Purchase tickets stage in seconds (after this time only one purchasing is allowed)
    uint256 public lotteryPurchaseStage = 3600;              // 1 hour

    /// @notice Allowed number of tickets purchased at a time
    uint256 public maxTicketsAmountPerTime = 200;

    /// @dev Counter for lottery IDs 
    uint256 private lotteryIdCounter = 0;

    /// @dev Counter for lottery tickets
    uint256 private ticketsCounter = 0;


    /// @dev Owners of TrueLotteryCoin
    address[] public owners;
    mapping (address => bool) public isOwner;
 
    /// @dev Allowance amounts on behalf of others
    mapping(address => mapping(address => uint256)) internal allowances;

    /// @dev Owners' balances of TrueLotteryCoin
    mapping(address => uint256) internal balances;

    /// @notice Represents the status of the lottery
    enum Status {
        NotStarted,             // The lottery hasn't started yet
        PurchaseTickets,        // The lottery is open for ticket purchases 
        Closed,                 // The purchase stage is close, waiting for determining the winner
        Completed               // The lottery has been closed and the numbers drawn
    }

    /// @notice Info about lottery
    struct LotteryInfo {
        uint256 lotteryID;                                    // ID for lotto
        Status lotteryStatus;                                 // Current status of lottery
        uint256 startingTimestamp;                            // Block timestamp for start of purchase stage
        uint256 closingTimestamp;                             // Block timestamp for end of purchase stage
        uint256 prizePoolInTokens;                            // The amount of TLC for prize money
        address winner;                                       // Winner of lottery
    }

    /// @dev Purcased tickets among all players
    mapping(uint256 => address) private tickets;

    /// @dev LotteryID => Player address => Amount of tickets
    mapping(uint256 => mapping(address => uint256)) internal lotteryIdPlayerTicketAmount;

    /// @dev LotteryID => All players with not zero purchased tickets
    mapping(uint256 => address[]) internal lotteryIdPlayers;

    /// @notice Lottery ID's to info about all loterries
    mapping(uint256 => LotteryInfo) public allLotteries;


    /// @notice The standard EIP-20 transfer event
    event Transfer(address indexed from, address indexed to, uint256 amount);

    /// @notice An event thats emitted when someone deposits ether
    event Deposit(address owner, uint256 value);

    /// @notice The standard EIP-20 approval event
    event Approval(address indexed owner, address indexed spender, uint256 amount);

    /// @notice An event thats emitted when owner receives tokens
    event MintTokens(address receiver, uint256 value);

    /// @notice An event thats emitted when owner loses tokens
    event BurnTokens(address owner, uint256 value);

    /// @notice An event of adding the new owner of tokens
    event NewOwner(address new_owner);

    /// @notice An event of purchasing playing tickets by some owner of tokens
    event PurchasingTickets(address player, uint256 value);

    /// @notice An event of some player's victory
    event Winning(address winner, uint256 value);

    /// @notice An event of opening new lottery
    event OpeningLottery(uint256 lotteryId);

    /// @notice An event of closing of purchase stage
    event ClosingLottery(uint256 lotteryId);

    /// @notice An event of completing lottery
    event CompletingLottery(uint256 lotteryId);

    /// @notice An event of withdrawing ETH
    event Withdraw(uint256 amount);


    //-------------------------------------------------------------------------
    // ERC20 BASIC FUNCTIONS
    //-------------------------------------------------------------------------

    /**
     * @notice Get the number of tokens `spender` is approved to spend on behalf of `account`
     * @param account The address of the account holding the funds
     * @param spender The address of the account spending the funds
     * @return The number of tokens approved
     */
    function allowance(address account, address spender) external override view returns (uint256) {
        return allowances[account][spender];
    }

    /**
     * @notice Approve `spender` to transfer up to `amount` from `src`
     * @dev This will overwrite the approval amount for `spender`
     * @param spender The address of the account which may transfer tokens
     * @param amount The number of tokens that are approved
     * @return Whether or not the approval succeeded
     */
    function approve(address spender, uint256 amount) public virtual override returns (bool) {
        _approve(_msgSender(), spender, amount);
        return true;
    }

    function _approve(address owner, address spender, uint256 amount) internal virtual {
        require(owner != address(0), "ERC20: approve from the zero address");
        require(spender != address(0), "ERC20: approve to the zero address");

        allowances[owner][spender] = amount;
        emit Approval(owner, spender, amount);
    }

    /**
     * @notice Get the number of tokens held by the `account`
     * @param account The address of the account to get the balance of
     * @return The number of tokens held
     */
    function balanceOf(address account) public view virtual override returns (uint256) {
        return balances[account];
    }
    
    /**
     * @notice Transfer `amount` tokens from `msg.sender` to `dst`
     * @param recipient The address of the destination account
     * @param amount The number of tokens to transfer
     * @return Whether or not the transfer succeeded
     */
    function transfer(address recipient, uint256 amount) public virtual override returns (bool) {
        require(isOwner[msg.sender]);
        _transfer(_msgSender(), recipient, amount);
        return true;
    }

    /**
     * @notice Transfer `amount` tokens from `src` to `dst`
     * @param sender The address of the source account
     * @param recipient The address of the destination account
     * @param amount The number of tokens to transfer
     * @return Whether or not the transfer succeeded
     */
    function transferFrom(address sender, address recipient, uint256 amount) public virtual override returns (bool) {
        uint256 currentAllowance = allowances[sender][_msgSender()];
        require(currentAllowance >= amount, "ERC20: transfer amount exceeds allowance");

        _transfer(sender, recipient, amount);
        _approve(sender, _msgSender(), currentAllowance - amount);

        return true;
    }

    function _transfer(address sender, address recipient, uint256 amount) internal virtual {
        require(sender != address(0), "ERC20: transfer from the zero address");
        require(recipient != address(0), "ERC20: transfer to the zero address");

        if (!isOwner[recipient]) {
            isOwner[recipient] = true;
            owners.push(recipient);
            emit NewOwner(recipient);
        }
        uint256 senderBalance = balances[sender];
        require(senderBalance >= amount, "ERC20: transfer amount exceeds balance");
        balances[sender] = senderBalance - amount;
        balances[recipient] += amount;

        emit Transfer(sender, recipient, amount);
    }

    //-------------------------------------------------------------------------
    // STATE MODIFYING FUNCTIONS
    //-------------------------------------------------------------------------

    /**
     * @dev Initializing owner of the contract for accumulations of commissions
     */
    constructor() public {
        isOwner[msg.sender] = true;
        owners.push(msg.sender);
    }

    /**
     * @notice Purchasing tokens for ether: 1 TLC = 0.01 ETH
     * @dev Ether deposit
     */
    fallback() external payable {
        uint256 new_tokens = msg.value.mul(tokenPrice).div(1 ether);
        require(new_tokens > 0, "Lottery::deposit: you don't have enough ether to buy at least 1 TLC, 1 TLC = 0.01 ETH");
        if (!isOwner[msg.sender]) {
            isOwner[msg.sender] = true;
            owners.push(msg.sender);
            balances[msg.sender] = 0;
            emit NewOwner(msg.sender);
        }
        _mint(msg.sender, new_tokens);
        emit Deposit(msg.sender, msg.value);
    }

    /**
     * @notice Starting a new lottery by the owner of the contract
     * @dev Initializing new alllotteries[lotteryIdCounter]
     */
    function startLottery() external onlyOwner() {
        if (lotteryIdCounter != 0) {
            require(allLotteries[lotteryIdCounter].lotteryStatus == Status.Completed, "Lottery::startLottery: wait until this lottery is closed");
        }
        // Incrementing lottery ID 
        lotteryIdCounter = lotteryIdCounter.add(1);
        ticketsCounter = 0;
        uint256 lotteryId = lotteryIdCounter;
        Status lotteryStatus = Status.PurchaseTickets;
        uint256 startingTimestamp = block.timestamp;
        uint256 closingTimestamp = 0;
        uint256 prizePoolInTokens = 0;
        address winner = address(0);
        LotteryInfo memory newLottery = LotteryInfo(
            lotteryId,
            lotteryStatus,
            startingTimestamp,
            closingTimestamp,
            prizePoolInTokens,
            winner
        );
        allLotteries[lotteryId] = newLottery;
        emit OpeningLottery(lotteryId);
    }

    /**
     * @notice Purchasing lottery tickets for TLC: 1 TLC = 1 Lottery Ticket, not more than 200 tickets per one time
     * @dev Adding '_amount' tickets to msg.sender
     * @param _amount Amount of purchasing tickets by the owner
     */
    function buyTickets(uint256 _amount) external {
        require(isOwner[msg.sender], "Lottery::buyTickets: you need to purchase TLC for buying tickets, 1 TLC = 0.01 Ether");
        require(balanceOf(msg.sender) >= _amount, "Lottery::buyTickets: you don't have enough TLC on your balance");
        require(lotteryIdCounter != 0, "Lottery::buyTickets: Lottery hasn't started yet");
        require(allLotteries[lotteryIdCounter].lotteryStatus == Status.PurchaseTickets, "Lottery::buyTickets: Purchase stage of lottery is closed, wait for next lottery");
        require(_amount <= maxTicketsAmountPerTime, "Lottery::buyTickers: it is not possible to buy more than 200 tickets per one time");

        uint256 initial_value = ticketsCounter;
        ticketsCounter = ticketsCounter.add(_amount);

        for (uint i=initial_value; i<ticketsCounter; i++) {
            tickets[i] = msg.sender;
        }
        if (lotteryIdPlayerTicketAmount[lotteryIdCounter][msg.sender] == 0) {
            lotteryIdPlayers[lotteryIdCounter].push(msg.sender);
        }
        lotteryIdPlayerTicketAmount[lotteryIdCounter][msg.sender] = lotteryIdPlayerTicketAmount[lotteryIdCounter][msg.sender].add(_amount);

        _burn(msg.sender, _amount);
        allLotteries[lotteryIdCounter].prizePoolInTokens = allLotteries[lotteryIdCounter].prizePoolInTokens.add(_amount);

        emit PurchasingTickets(msg.sender, _amount);
    }

    /**
     * @notice Closing a lottery by the owner of the contract if more than an hour has passed and no transactions have been made after that
     * @dev Changing allLotteries[lotteryIdCounter].lotteryStatus
     */
    function closePurchaseStage() external onlyOwner() {
        require(block.timestamp.sub(allLotteries[lotteryIdCounter].startingTimestamp) > lotteryPurchaseStage
                && allLotteries[lotteryIdCounter].prizePoolInTokens > 1, "1 hour hasn't passed yet or less than 1 ticket was bought");
        allLotteries[lotteryIdCounter].lotteryStatus = Status.Closed;
        emit ClosingLottery(lotteryIdCounter);
    }

    /**
     * @notice Complete a lottery by the owner of the contract when the lottery is closed and pay out the win
     * @dev Generating random number and transfer prizePoolInTokens to the winner
     */
    function completeLottery() external onlyOwner() {
        require(allLotteries[lotteryIdCounter].lotteryStatus == Status.Closed, "Lottery::buyTickets: it is not possible to close lottery right now");
        allLotteries[lotteryIdCounter].closingTimestamp = block.timestamp;
        uint256 winningTicket = _drawWinningNumber();
        _determiningWinnerAndPayout(winningTicket);
        allLotteries[lotteryIdCounter].lotteryStatus = Status.Completed;
        emit CompletingLottery(lotteryIdCounter);
    }

    /**
     * @notice Withdrawing ether on your account
     * @dev Transfer '_amount' tokens to ether on account of msg.sender
     * @param _amount Amount of withdrawing tokens from account
     */
    function withdraw(uint256 _amount) external {
        require(balances[msg.sender] >= _amount, "Lottery::withdraw: you don't have enough tokens to withdraw");
        
        uint256 etherWithdraw = _amount.mul(1 ether).div(tokenPrice);
        msg.sender.transfer(etherWithdraw);
        emit Withdraw(etherWithdraw);
        _burn(msg.sender, _amount);
    }

    //-------------------------------------------------------------------------
    // INTERNAL FUNCTIONS
    //-------------------------------------------------------------------------

    /**
     * @dev Generating random number of winner ticket
     * @return The number of winner ticket
     */
    function _drawWinningNumber() internal onlyOwner() returns(uint256) {
        uint256 winningNumber = uint256(keccak256(abi.encodePacked(block.difficulty, now))) % ticketsCounter;
        return winningNumber;
    }

    /**
     * @dev Saving the winner and payout of winnings
     * @param _winningNumber Number of winning ticket in lottery
     */
    function _determiningWinnerAndPayout(uint256 _winningNumber) internal onlyOwner() {
        address lotteryWinner = tickets[_winningNumber];
        allLotteries[lotteryIdCounter].winner = lotteryWinner;

        // commission 1 token to the owner of the contract
        _mint(lotteryWinner, allLotteries[lotteryIdCounter].prizePoolInTokens.sub(1));
        _mint(owner(), 1);

        emit Winning(lotteryWinner, allLotteries[lotteryIdCounter].prizePoolInTokens);
    }

    /**
     * @dev Creates '_tokens' tokens and assigns them to `_account`, increasing the total supply
     * @param _account Owner's account of the TrueLotteryCoin
     * @param _tokens Value of tokens
     */
    function _mint(address _account, uint256 _tokens) internal {
        require(isOwner[_account], "Lottery::_mint: mint to non-owner");

        totalSupply = totalSupply.add(_tokens);
        balances[_account] = balances[_account].add(_tokens);
        emit MintTokens(_account, _tokens);
    }

    /**
     * @dev Destroys '_tokens' tokens from `_account`, decreasing the total supply
     * @param _account Owner's account of the TrueLotteryCoin
     * @param _tokens Value of tokens
     */
    function _burn(address _account, uint256 _tokens) internal {
        require(isOwner[_account], "Lottery::_burn: burn from non-owner");

        totalSupply = totalSupply.sub(_tokens);
        balances[_account] = balances[_account].sub(_tokens);
        emit BurnTokens(_account, _tokens);
    }

    //-------------------------------------------------------------------------
    // VIEW FUNCTIONS
    //-------------------------------------------------------------------------

    /**
     * @notice Get the list of addresses who purchased tickets in the current lottery
     * @return List of players
     */
    function getAllTicketOwners() public view returns (address[] memory) {
        return lotteryIdPlayers[lotteryIdCounter];
    }

    /**
     * @notice Get the list of addresses who purchased tickets in the '_lotteryId' lottery
     * @param _lotteryId Id of the lottery
     * @return List of players
     */
    function getAllTicketOwnersInLotteryId(uint256 _lotteryId) public view returns (address[] memory) {
        return lotteryIdPlayers[_lotteryId];
    }

    /**
     * @notice Get the number of purchased tickets by '_player' address in the current lottery
     * @param _player Owner's address
     * @return Amount of purchased tickets
     */
    function getAmountOfTickets(address _player) public view returns (uint256) {
        return lotteryIdPlayerTicketAmount[lotteryIdCounter][_player];
    }

    /**
     * @notice Get the number of purchased tickets by '_player' address in the '_lotteryId' lottery
     * @param _player Owner's address
     * @param _lotteryId Id of the lottery
     * @return Amount of purchased tickets
     */
    function getAmountOfTicketsInLotteryId(address _player, uint256 _lotteryId) public view returns (uint256) {
        return lotteryIdPlayerTicketAmount[_lotteryId][_player];
    }

    /**
     * @notice Get the number of total purchased tickets in the current lottery (prize pool in tokens)
     * @return Amount of total purchased tickets
     */
    function getCurrentTotalPurchasedTickets() public view returns (uint256) {
        return allLotteries[lotteryIdCounter].prizePoolInTokens;
    }

    /**
     * @notice Get the number of total purchased tickets in the '_lotteryId' lottery (prize pool in tokens)
     * @param _lotteryId Id of the lottery
     * @return Amount of total purchased tickets
     */
    function getTotalPurchasedTicketsInLotteryId(uint256 _lotteryId) public view returns (uint256) {
        return allLotteries[_lotteryId].prizePoolInTokens;
    }

    /**
     * @notice Get the chance of winning by the '_player' address in percents (round down)
     * @param _player Address of player
     * @return Chance of winning in percents if more than 0.99
     */
    function getChanceOfWinning(address _player) external view returns (uint256) {
        uint256 playerTickets = getAmountOfTickets(_player);
        require(playerTickets != 0, "You haven't purchased tickets yet");
        uint256 totalTickets = getCurrentTotalPurchasedTickets();
        require(totalTickets != 0, "Nobody has purchased tickets yet");
        return playerTickets.mul(100).div(totalTickets);
    }

    /**
     * @notice Get the id of the current lottery
     */
    function getCurrentLotteryId() public view returns (uint256) {
        return lotteryIdCounter;
    }

    /**
     * @notice Get the status of the current lottery
     */
    function getCurrentLotteryStatus() external view returns (string memory) {
        uint256 curStatus = uint256(allLotteries[lotteryIdCounter].lotteryStatus);
        if (curStatus == 0) {
            return "NotStarted";
        }
        else if (curStatus == 1) {
            return "PurchaseTickets";
        }
        else if (curStatus == 2) {
            return "Closed";
        }
        else {
            return "Completed";
        }
    }

    /**
     * @notice Get the status of the '_lotteryId' lottery
     * @param _lotteryId Id of the lottery
     */
    function getLotteryStatus(uint256 _lotteryId) public view returns (Status) {
        return allLotteries[_lotteryId].lotteryStatus;
    }

    /**
     * @notice Get the winner of the last lottery
     * @return The address of previous winner
     */
    function getWinnerOfLottery() public view returns (address) {
        require(lotteryIdCounter != 0, "It is first lottery");
        if (allLotteries[lotteryIdCounter].lotteryStatus == Status.Completed) {
            return allLotteries[lotteryIdCounter].winner;
        }
        else {
            return allLotteries[lotteryIdCounter.sub(1)].winner;
        }
    }

    /**
     * @notice Get the winner of the '_lotteryId' lottery
     * @param _lotteryId Id of the lottery
     * @return The address of winner
     */
    function getWinnerOfLotteryId(uint256 _lotteryId) public view returns (address) {
        return allLotteries[_lotteryId].winner;
    }
}
