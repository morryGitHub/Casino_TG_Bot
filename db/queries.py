"""USERS"""

INSERT_USER_INTO_USERS = """
    INSERT INTO Users (user_id,chat_id, username, active) VALUES (%s, %s, %s, %s)
"""

CHECK_USER_EXISTS = """
    SELECT EXISTS(SELECT 1 FROM Users WHERE user_id = %s)
"""

UPDATE_USER_ACTIVE = """
    UPDATE Users SET active = %s WHERE user_id = %s
"""

UPDATE_USER_LANG = """
    UPDATE Users SET language = %s WHERE user_id = %s
"""

SELECT_USER_LANG = """
    SELECT language FROM Users WHERE user_id = %s
"""

SELECT_USER_ACTIVITY = """
    SELECT active FROM Users WHERE user_id = %s
"""

SELECT_USER_LASTBONUS = """
    SELECT last_bonus FROM Users WHERE user_id = %s
"""

UPDATE_USER_LASTBONUS = """
    UPDATE Users SET last_bonus = %s WHERE user_id = %s
"""

"""BALANCES"""

SELECT_BALANCE = """
    SELECT balance FROM Balances WHERE user_id = %s
"""

INSERT_USER_INTO_BALANCES = """
    INSERT INTO Balances (user_id, balance) VALUES (%s, %s)
"""

UPDATE_BALANCE_BEFORE_SPIN = """
    UPDATE Balances SET balance = balance - %s WHERE user_id = %s

"""

UPDATE_BALANCE_AFTER_SPIN = """
    UPDATE Balances SET balance = balance + %s WHERE user_id = %s

"""

UPDATE_BALANCE = """
    UPDATE Balances SET balance = balance + %s WHERE user_id = %s
"""

"""RESULTS"""

INSERT_USER_INTO_RESULTS = """
    INSERT INTO Results (user_id, winCoin, loseCoin, maxWin, maxBet) VALUES (%s, %s, %s, %s, %s)
"""

SELECT_MAXWIN_RESULTS = """
    SELECT maxWin FROM Results WHERE user_id = %s
"""

SELECT_MAXBET_RESULTS = """
    SELECT maxBet FROM Results WHERE user_id = %s
"""

SELECT_DATA_FROM_RESULTS = """
    SELECT winCoin, loseCoin, maxWin, maxBet FROM Results where user_id = %s
"""

UPDATE_WIN_RESULTS = """
    UPDATE Results SET winCoin = winCoin + %s WHERE user_id = %s
"""

UPDATE_LOST_RESULTS = """
    UPDATE Results SET loseCoin = loseCoin + %s WHERE user_id = %s

"""

UPDATE_MAXWIN_RESULTS = """
    UPDATE Results SET maxWin = maxWin + %s WHERE user_id = %s
"""

UPDATE_MAXBET_RESULTS = """
    UPDATE Results SET maxBet = maxBet + %s WHERE user_id = %s

"""
