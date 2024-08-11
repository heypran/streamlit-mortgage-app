import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from decimal import Decimal, getcontext

# Set high precision for decimal calculations
getcontext().prec = 40

# Uniswap V3 constants
MIN_TICK = -887272
MAX_TICK = 887272
Q96 = Decimal(2**96)
SQRT_PRICE_1_1 = Decimal('79228162514264337593543950336')  # sqrt(1) * 2^96

# Uniswap V3 math functions
def tick_to_sqrt_price(tick):
    return Decimal(1.0001) ** (Decimal(tick) / 2) * Q96

def sqrt_price_to_tick(sqrt_price):
    return int((Decimal(sqrt_price) / Q96).ln() * 2 / Decimal(1.0001).ln())

def get_next_sqrt_price(sqrt_price, liquidity, amount, zero_for_one):
    if zero_for_one:
        return sqrt_price - (Decimal(amount) * Q96) // liquidity
    else:
        return sqrt_price + (Decimal(amount) * Q96) // liquidity

def compute_swap(sqrt_price_current, liquidity, amount, zero_for_one):
    sqrt_price_target = get_next_sqrt_price(sqrt_price_current, liquidity, amount, zero_for_one)
    
    if zero_for_one:
        amount0 = (liquidity * abs(sqrt_price_current - sqrt_price_target)) // (sqrt_price_current * sqrt_price_target)
        amount1 = liquidity * abs(sqrt_price_current - sqrt_price_target) // Q96
    else:
        amount0 = (liquidity * abs(sqrt_price_current - sqrt_price_target)) // (sqrt_price_current * sqrt_price_target)
        amount1 = liquidity * abs(sqrt_price_current - sqrt_price_target) // Q96
    
    return sqrt_price_target, amount0, amount1

# Initialize session state
if 'pool' not in st.session_state:
    st.session_state.pool = None
if 'positions' not in st.session_state:
    st.session_state.positions = []

# App title
st.title("Uniswap V3 Liquidity Pool Simulator")

# Create pool section
st.header("Create Liquidity Pool")
token0 = st.text_input("Token 0 Symbol", "USDC")
token1 = st.text_input("Token 1 Symbol", "ETH")
tick_spacing = st.number_input("Tick Spacing", min_value=1, value=60)
sqrt_price_x96 = st.text_input("Initial sqrt_price_x96", value=str(SQRT_PRICE_1_1))
fee_ppm = st.number_input("Fee (in parts per million)", min_value=1, max_value=1000000, value=3000)

if st.button("Create Pool"):
    try:
        sqrt_price_x96_decimal = Decimal(sqrt_price_x96)
        st.session_state.pool = {
            "token0": token0,
            "token1": token1,
            "tick_spacing": tick_spacing,
            "sqrt_price_x96": sqrt_price_x96_decimal,
            "fee_ppm": fee_ppm,
            "current_tick": sqrt_price_to_tick(sqrt_price_x96_decimal),
            "liquidity": Decimal(0)
        }
        st.success(f"Pool created: {token0}/{token1} with {fee_ppm} ppm fee")
        st.write(f"Current tick: {st.session_state.pool['current_tick']}")
    except:
        st.error("Invalid sqrt_price_x96 value. Please enter a valid number.")

# Add liquidity section
if st.session_state.pool:
    st.header("Add Liquidity")
    liquidity_delta = st.number_input("Liquidity Delta", min_value=0, value=1000000)
    min_tick = st.number_input("Min Tick", value=st.session_state.pool['current_tick'] - 1000)
    max_tick = st.number_input("Max Tick", value=st.session_state.pool['current_tick'] + 1000)

    if st.button("Add Liquidity"):
        st.session_state.positions.append({
            "min_tick": min_tick,
            "max_tick": max_tick,
            "liquidity": Decimal(liquidity_delta)
        })
        st.session_state.pool["liquidity"] += Decimal(liquidity_delta)
        st.success("Liquidity added successfully!")

    # Trade section
    st.header("Place Trade")
    trade_amount = st.number_input("Trade Amount", min_value=0.0, value=1.0, step=0.1)
    trade_token = st.selectbox("Token to Trade", [st.session_state.pool["token0"], st.session_state.pool["token1"]])
    trade_direction = st.selectbox("Trade Direction", ["Buy", "Sell"])

    if st.button("Execute Trade"):
        zero_for_one = (trade_token == st.session_state.pool["token1"]) if (trade_direction == "Buy") else (trade_token == st.session_state.pool["token0"])
        
        new_sqrt_price, amount0, amount1 = compute_swap(
            st.session_state.pool["sqrt_price_x96"],
            st.session_state.pool["liquidity"],
            trade_amount,
            zero_for_one
        )
        
        st.session_state.pool["sqrt_price_x96"] = new_sqrt_price
        st.session_state.pool["current_tick"] = sqrt_price_to_tick(new_sqrt_price)
        
        st.success(f"Trade executed. New tick: {st.session_state.pool['current_tick']}")
        st.write(f"Amount of {st.session_state.pool['token0']} traded: {amount0}")
        st.write(f"Amount of {st.session_state.pool['token1']} traded: {amount1}")

    # Display positions
    st.header("Liquidity Positions")
    for i, position in enumerate(st.session_state.positions):
        st.write(f"Position {i+1}: Tick Range [{position['min_tick']}, {position['max_tick']}], Liquidity: {position['liquidity']}")

# Generate liquidity graph
    st.header("Liquidity Graph")

    if st.session_state.positions:
        # Find the range of ticks to display
        min_graph_tick = min(MIN_TICK, min(position['min_tick'] for position in st.session_state.positions))
        max_graph_tick = max(MAX_TICK, max(position['max_tick'] for position in st.session_state.positions))
        
        # Create a dictionary to store liquidity at each tick
        liquidity_at_tick = {}
        
        # Populate the liquidity
        for position in st.session_state.positions:
            min_tick = position['min_tick']
            max_tick = position['max_tick']
            liquidity = position['liquidity']
            
            for tick in range(min_tick, max_tick + 1):
                if tick not in liquidity_at_tick:
                    liquidity_at_tick[tick] = 0
                liquidity_at_tick[tick] += liquidity
        
        # Sort the ticks and get the corresponding liquidity
        sorted_ticks = sorted(liquidity_at_tick.keys())
        liquidity_values = [liquidity_at_tick[tick] for tick in sorted_ticks]
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.step(sorted_ticks, liquidity_values, where='post')
        ax.set_xlabel('Tick')
        ax.set_ylabel('Liquidity')
        ax.set_title('Liquidity Distribution')
        
        # Add vertical line for current tick
        current_tick = st.session_state.pool['current_tick']
        ax.axvline(x=current_tick, color='r', linestyle='--', label='Current Tick')
        
        # Add labels for token0 and token1
        ax.text(current_tick + 10, ax.get_ylim()[1], st.session_state.pool['token1'], verticalalignment='top')
        ax.text(current_tick - 10, ax.get_ylim()[1], st.session_state.pool['token0'], horizontalalignment='right', verticalalignment='top')
        
        ax.legend()
        st.pyplot(fig)
    else:
        st.write("Add liquidity positions to see the graph.")
else:
    st.write("Create a pool first to add liquidity and see the graph.")

# Add more liquidity button
if st.session_state.pool and st.button("Add More Liquidity"):
    st.experimental_rerun()