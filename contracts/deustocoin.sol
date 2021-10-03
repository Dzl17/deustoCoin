// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.7.0 <0.9.0;

/// @title ERC20-based token used in the Deustocoin project for the University of Deusto
contract Deustocoin {
    string private constant _name = "Deustocoin";
    string private constant _symbol = "UDC";
    uint8 private constant _decimals = 2; // number of decimals the coin can be divided in, equivalent to euro in this case
    uint256 private _totalSupply = 0; // Total supply of tokens in circulation, depends on the _mint() and _burn() calls
    address _contractOwner; // Account that deploys the contract (the project administrator, e.g. the University of Deusto)

    mapping(address => uint256) balances; // Balances of users, saved with 2 decimals (the value is equivalent to cents)

    /// @notice MUST trigger when tokens are transferred, including zero value transfers
    /// @dev a token contract which creates new tokens SHOULD trigger the event with _from set to 0x0 when tokens are created
    event Transfer(
        address indexed _from, 
        address indexed _to, 
        uint256 _value
    );

    /// @notice good action done by the user
    event Action(
        address indexed _from,
        address indexed _who,
        uint256 indexed _actionID,
        uint256 _reward,
        uint256 _time,
        bytes32 _ipfsHash
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
    function totalSupply() public view returns (uint256) {
        return _totalSupply;
    }

    /// @notice returns the account balance of the account with address _owner
    /// @return balance balance of _owner account
    function balanceOf(address _owner) public view returns (uint256 balance) {
        return balances[_owner];
    }

    /// @notice transfers _value amount of tokens to address _to
    /// @dev it MUST fire the Transfer event (even with value 0), and SHOULD throw if the message caller's acount doesn't have enough balance
    /// @return success of the operation
    function transfer(address _to, uint256 _value)
        public
        returns (bool success)
    {
        require(balances[msg.sender] >= _value); // Must have enough balance
        require(_to != _contractOwner && _to != address(0)); // Avoid transferring to the contract owner account or the 0x00..0 account
        balances[msg.sender] -= _value;
        balances[_to] += _value;
        emit Transfer(msg.sender, _to, _value);
        return true;
    }

    /// @notice mints an amount of UDCs to the _to address; only an administrator can perform the operation
    /// @dev a transfer event is emitted noting that the tokens come from the 0x00...0 address
    function mint(address _to, uint256 _value) public {
        require(_to != address(0)); // Do not mint to 0x00...0
        require(msg.sender == _contractOwner); // Only the owner can mint
        _totalSupply += _value;
        balances[_to] += _value;
        emit Transfer(address(0), _to, _value);
    }

    /// @notice burns an amount of UDCs from the _from address; only an administrator can perform the operation
    /// @dev a transfer event is emitted noting that the tokens are sent to the 0x00...0 address
    function burn(address _from, uint256 _value) public {
        require(_from != address(0)); // Do not burn from 0x00..0
        require(balances[_from] >= _value); // _from address' balance must be enough
        require(msg.sender == _contractOwner); // Only the owner can burn

        _totalSupply -= _value;
        balances[_from] -= _value;
        emit Transfer(_from, address(0), _value);
    }

    /// @notice registers a collaborator's good action in the blockchain and rewards them
    function processAction(
        address _from,      // Promoter
        address _to,        // Collaborator
        uint256 _actionID,
        uint256 _value,     // Reward for the action
        uint256 _time,      // When does the action happen
        bytes32 _ipfsHash   // Hash of the action proof image
    ) public returns (bool success) {
        require(msg.sender == _contractOwner);   // Only the owner can register an action
        require(balances[_from] >= _value);

        require(_to != _contractOwner && _to != address(0)); // Avoid transferring to the contract owner account or the 0x00..0 account
        balances[_from] -= _value;
        balances[_to] += _value;
        emit Action(_from, _to, _actionID, _value, _time, _ipfsHash);
        return true;
    }
}
