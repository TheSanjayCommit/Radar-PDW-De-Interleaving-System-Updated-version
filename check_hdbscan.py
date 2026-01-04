
try:
    from sklearn.cluster import HDBSCAN
    print("HDBSCAN available in sklearn")
except ImportError:
    print("HDBSCAN NOT in sklearn")
    try:
        import hdbscan
        print("hdbscan package available")
    except ImportError:
        print("hdbscan NOT available")
