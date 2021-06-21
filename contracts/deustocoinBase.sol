// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.7.0 <0.9.0;

// TODO: reduce gas cost (not really important) https://betterprogramming.pub/how-to-write-smart-contracts-that-optimize-gas-spent-on-ethereum-30b5e9c5db85
// TODO: use SafeMath for security
// TODO: adapt the contract to the deustocoin specification (difference between users and promoters)

/// @title ERC20 compliant token used in the Deustocoin project for the University of Deusto
contract Deustocoin{
    string  private constant _name = "Deustocoin";
    string  private constant _symbol = "UDC";
    uint8   private constant _decimals = 2; // number of decimals the coin can be divided in, equivalent to euro in this case
    uint256 private constant _totalSupply = 1000000;  // TODO: specify initial amount
    address _contractOwner; // Account that deploys the contract (the project administrator, e.g. the University of Deusto) 

    mapping(address => uint256) balances;   // Balances of users
    mapping(address => mapping (address => uint256)) allowed;   // Accounts approved to withdraw from a given account + sum allowed


    /// @notice MUST trigger when tokens are transferred, including zero value transfers
    /// @dev a token contract which creates new tokens SHOULD trigger the event with _from set to 0x0 when tokens are created
    event Transfer(
        address indexed _from, 
        address indexed _to, 
        uint256 _value
    );

    /// @notice MUST trigger on any successful call to approve()
    event Approval(
        address indexed _owner, 
        address indexed _spender, 
        uint256 _value
    );


    constructor() {
        _contractOwner = msg.sender;
        balances[msg.sender] = _totalSupply;
    }

    /// @notice returns the name of the token
    /// @return token name
    function name() public pure returns (string memory) {
        return _name;
    }

    /// @notice returns the symbol of the token
    /// @return token symbol
    function symbol() public pure returns (string memory) {
        return _symbol;
    }

    /// @notice returns the number of decimals the token uses
    /// @return token decimals
    function decimals() public pure returns (uint8) {
        return _decimals;
    }

    /// @notice returns the total token supply
    /// @return total token supply
    function totalSupply() public pure returns (uint256) {
        return _totalSupply;
    }

    /// @notice returns the account balance of the account with address _owner
    /// @return balance of _owner account
    function balanceOf(address _owner) public view returns (uint256 balance) {
        return balances[_owner];
    }

    /// @notice transfers _value amount of tokens to address _to
    /// @dev it MUST fire the Transfer event (even with value 0), and SHOULD throw if the message caller's acount doesn't have enough balance
    /// @return success of the operation
    function transfer(address _to, uint256 _value) public returns (bool success) {
        require(balances[msg.sender] >= _value);    // Must have enough balance
        balances[msg.sender] -= _value;
        balances[_to] += _value;
        emit Transfer(msg.sender, _to, _value);
        return true;
    }

    /// @notice transfers _value amount of tokens from address _from to address _to
    /// @dev it MUST fire the Transfer event (even with value 0), and SHOULD throw unless _from account has deliberately authorized the sender of the message via some mechanism
    /// @return success of the operation
    function transferFrom(address _from, address _to, uint256 _value) public returns (bool success) {
        uint256 currentAllowance = allowed[_from][msg.sender];  // How much can be transferred
        require(balances[_from] >= _value && currentAllowance >= _value);
        balances[_to] += _value;
        balances[_from] -= _value;
        allowed[_from][msg.sender] -= _value;   // Reduce the remaining allowance
        emit Transfer(_from, _to, _value);
        return true;
    }

    /// @notice allows _spender to withdraw from your account multiple times, up to the _value amount. If called again it overwrites the current allowance with _value
    /// @return success of the operation
    function approve(address _spender, uint256 _value) public returns (bool success) {
        allowed[msg.sender][_spender] = _value;
        emit Approval(msg.sender, _spender, _value);
        return true;
    }

    /// @notice returns the amount which _spender is allowed to withdraw from _owner
    /// @return remaining allowed withdrawal amount
    function allowance(address _owner, address _spender) public view returns (uint256 remaining) {
        return allowed[_owner][_spender];
    }
}