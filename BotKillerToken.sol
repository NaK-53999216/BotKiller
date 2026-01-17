// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract BotKillerToken {
    string public name = "BotKiller Token";
    string public symbol = "BOKI";
    uint8 public decimals = 18;

    uint256 public totalSupply;

    address public constant FOUNDER_WALLET = 0x83E4ab9497146B66e3b4ea307Dff2C5f58e65622;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    // Ownership (minimal)
    address public owner;
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    modifier onlyOwner() {
        require(msg.sender == owner, "ONLY_OWNER");
        _;
    }

    // --- Staking (for auditors / enterprises) ---
    // Companies stake Coin B to be considered "auditors".
    mapping(address => uint256) public stakedBalance;
    uint256 public totalStaked;
    uint256 public minStakeToBeAuditor;

    event Staked(address indexed staker, uint256 amount);
    event Unstaked(address indexed staker, uint256 amount);
    event MinStakeUpdated(uint256 oldValue, uint256 newValue);

    constructor() {
        require(FOUNDER_WALLET != address(0), "FOUNDER_WALLET_ZERO");

        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);

        // Fixed supply: 100,000,000 tokens
        uint256 supply = 100_000_000 * (10 ** uint256(decimals));
        totalSupply = supply;

        // 5% to founder at launch (deployment)
        uint256 founderAllocation = 5_000_000 * (10 ** uint256(decimals));
        balanceOf[FOUNDER_WALLET] = founderAllocation;
        emit Transfer(address(0), FOUNDER_WALLET, founderAllocation);

        // Remaining supply to deployer (treasury / protocol-controlled address)
        uint256 remaining = supply - founderAllocation;
        balanceOf[msg.sender] = remaining;
        emit Transfer(address(0), msg.sender, remaining);

        // Default minimum stake (can be updated by owner)
        minStakeToBeAuditor = 10_000 * (10 ** uint256(decimals));
        emit MinStakeUpdated(0, minStakeToBeAuditor);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        _transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        uint256 allowed = allowance[from][msg.sender];
        require(allowed >= value, "ALLOWANCE_TOO_LOW");
        allowance[from][msg.sender] = allowed - value;
        _transfer(from, to, value);
        return true;
    }

    function _transfer(address from, address to, uint256 value) internal {
        require(to != address(0), "TO_ZERO");
        uint256 bal = balanceOf[from];
        require(bal >= value, "BALANCE_TOO_LOW");
        balanceOf[from] = bal - value;
        balanceOf[to] += value;
        emit Transfer(from, to, value);
    }

    // --- Ownership ---
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "NEW_OWNER_ZERO");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    // --- Staking ---
    function setMinStakeToBeAuditor(uint256 newMinStake) external onlyOwner {
        uint256 old = minStakeToBeAuditor;
        minStakeToBeAuditor = newMinStake;
        emit MinStakeUpdated(old, newMinStake);
    }

    function isAuditor(address account) external view returns (bool) {
        return stakedBalance[account] >= minStakeToBeAuditor;
    }

    function stake(uint256 amount) external returns (bool) {
        require(amount > 0, "AMOUNT_ZERO");

        // Transfer tokens into the contract as stake
        _transfer(msg.sender, address(this), amount);

        stakedBalance[msg.sender] += amount;
        totalStaked += amount;

        emit Staked(msg.sender, amount);
        return true;
    }

    function unstake(uint256 amount) external returns (bool) {
        require(amount > 0, "AMOUNT_ZERO");

        uint256 staked = stakedBalance[msg.sender];
        require(staked >= amount, "STAKED_TOO_LOW");

        stakedBalance[msg.sender] = staked - amount;
        totalStaked -= amount;

        // Return staked tokens back to the staker
        _transfer(address(this), msg.sender, amount);

        emit Unstaked(msg.sender, amount);
        return true;
    }
}
