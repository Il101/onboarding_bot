import bcrypt

password = "admin"
# The hash I put in .env
hash_from_env = "$2b$12$K8F.Y3K.iK1Z/p0Y.mG6e.F5u7G8h9i0j1k2l3m4n5o6p7q8r9s0t"

try:
    match = bcrypt.checkpw(password.encode(), hash_from_env.encode())
    print(f"Match: {match}")
except Exception as e:
    print(f"Error: {e}")
