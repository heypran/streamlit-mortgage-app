import json
import streamlit as st
import matplotlib.pyplot as plt
from web3 import Web3

# Connect to local Ethereum node
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Contract ABI
contract_abi = json.loads('''[
  {
    "inputs": [
      { "internalType": "string", "name": "name", "type": "string" },
      { "internalType": "string", "name": "symbol", "type": "string" },
      { "internalType": "uint256", "name": "_initialSupply", "type": "uint256" },
      { "internalType": "uint256", "name": "_initialPricePerToken", "type": "uint256" }
    ],
    "stateMutability": "nonpayable",
    "type": "constructor"
  },
  {
    "inputs": [
      { "internalType": "uint256", "name": "_ethAmount", "type": "uint256" }
    ],
    "name": "calculatePurchaseReturn",
    "outputs": [
      { "internalType": "uint256", "name": "", "type": "uint256" }
    ],
    "stateMutability": "view",
    "type": "function"
  }
]''')

# Streamlit app
st.title('Bancor Continuous Token Bonding Curve')

# Input for contract address
contract_address = st.text_input('Enter Contract Address:', '')

# Connect to the contract
if Web3.is_address(contract_address):
    contract_address = Web3.toChecksumAddress(contract_address)
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    # Input fields for ETH amount
    eth_amount = st.number_input('Enter ETH amount:', min_value=0.0, step=0.01)

    # Button to calculate token amount
    if st.button('Calculate Token Amount'):
        eth_amount_wei = Web3.toWei(eth_amount, 'ether')
        token_amount = contract.functions.calculatePurchaseReturn(eth_amount_wei).call()
        st.write(f'Token Amount: {Web3.fromWei(token_amount, "ether")}')

    # Generate bonding curve
    eth_values = [i for i in range(1, 101)]  # ETH amounts from 1 to 100
    token_values = []

    for eth in eth_values:
        eth_wei = Web3.toWei(eth, 'ether')
        token_amount = contract.functions.calculatePurchaseReturn(eth_wei).call()
        token_values.append(Web3.fromWei(token_amount, 'ether'))

    # Plot bonding curve
    plt.figure(figsize=(10, 5))
    plt.plot(eth_values, token_values, label='Bonding Curve')
    plt.xlabel('ETH Amount')
    plt.ylabel('Token Amount')
    plt.title('Bonding Curve')
    plt.legend()
    st.pyplot(plt)
else:
    st.write("Please enter a valid contract address.")
