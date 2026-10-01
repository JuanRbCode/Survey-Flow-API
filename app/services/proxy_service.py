import os

def load_proxy_pool():
    """Carga la lista de proxies desde el archivo proxy_list.txt"""
    proxy_pool = [None] # Por defecto una petición limpia sin proxy
    
    proxy_file_path = os.path.join(os.getcwd(), "proxy_list.txt")
    if os.path.exists(proxy_file_path):
        try:
            with open(proxy_file_path, "r") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        proxy_pool.append({
                            "server": f"http://{line}"
                        })
        except Exception as e:
            print(f"Error cargando proxy_list.txt: {e}")
            
    return proxy_pool