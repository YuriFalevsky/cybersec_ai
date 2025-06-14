import subprocess
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Directory to store recon results
def get_results_dir():
    results_dir = os.path.join('results', 'recon')
    os.makedirs(results_dir, exist_ok=True)
    return results_dir

# Utility runner
def run_command(command, output_file=None):
    print(f"[RECON] Running: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=600)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
        return result.stdout
    except Exception as e:
        print(f"[RECON] Error running command: {e}")
        return None

# Recon functions
def identify_web_server(url, output_file=None):
    command = f"whatweb {url}"
    return run_command(command, output_file)

def enumerate_subdomains(domain, wordlist=None, output_file=None):
    command = f"sublist3r -d {domain} -o {output_file or os.path.join(get_results_dir(), 'subdomains.txt')}"
    return run_command(command, output_file)

def brute_force_directories(url, wordlist, output_file=None):
    command = f"ffuf -w {wordlist} -u {url}/FUZZ -of json -o {output_file or os.path.join(get_results_dir(), 'ffuf_dirs_files.json')} -e '.php,.txt,.bak,.old,.zip,.tar,.tar.gz'"
    return run_command(command, output_file)

def discover_vhosts(domain, vhost_wordlist, output_file=None):
    command = f"ffuf -w {vhost_wordlist} -u http://{domain} -H 'Host: FUZZ.{domain}' -o {output_file or os.path.join(get_results_dir(), 'vhosts.json')} -of json"
    return run_command(command, output_file)

def gather_dns_info(domain, output_file=None):
    command = f"dig {domain} any +nocmd +multiline +noquestion +answer"
    output = run_command(command)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output or '')
    return output

def nmap_scan(target, output_file=None):
    command = f"nmap -sT -A -Pn {target} -oN {output_file or os.path.join(get_results_dir(), 'nmap.txt')}"
    return run_command(command, output_file)

def subdomain_fuzz_ffuf(domain, wordlist, output_file=None):
    command = f"ffuf -w {wordlist} -u http://FUZZ.{domain} -of json -o {output_file or os.path.join(get_results_dir(), 'ffuf_subdomains.json')}"
    return run_command(command, output_file)

@app.route("/recon", methods=["GET", "POST"])
def recon_page():
    if request.method == "POST":
        target_url = request.form.get("target_url")
        target_domain = request.form.get("target_domain")
        dir_wordlist = request.form.get("dir_wordlist")
        sub_wordlist = request.form.get("sub_wordlist")
        vhost_wordlist = request.form.get("vhost_wordlist")

        results_dir = get_results_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        web_output = identify_web_server(target_url, os.path.join(results_dir, f'whatweb_{timestamp}.txt'))
        subdomains_output = enumerate_subdomains(target_domain, sub_wordlist or None, os.path.join(results_dir, f'subdomains_{timestamp}.txt')) if sub_wordlist else "[RECON] Skipped subdomain enumeration."
        dirs_output = brute_force_directories(target_url, dir_wordlist, os.path.join(results_dir, f'ffuf_dirs_{timestamp}.json')) if dir_wordlist else "[RECON] Skipped dir brute-force."
        vhosts_output = discover_vhosts(target_domain, vhost_wordlist or dir_wordlist, os.path.join(results_dir, f'vhosts_{timestamp}.json')) if vhost_wordlist or dir_wordlist else "[RECON] Skipped vhost discovery."
        dns_output = gather_dns_info(target_domain, os.path.join(results_dir, f'dns_{timestamp}.txt'))
        subfuzz_output = subdomain_fuzz_ffuf(target_domain, sub_wordlist, os.path.join(results_dir, f'ffuf_subdomains_{timestamp}.json')) if sub_wordlist else "[RECON] Skipped subdomain ffuf."
        nmap_output = nmap_scan(target_domain, os.path.join(results_dir, f'nmap_{timestamp}.txt'))

        return render_template("recon_result.html", web_output=web_output, subdomains_output=subdomains_output, dirs_output=dirs_output,
                               vhosts_output=vhosts_output, dns_output=dns_output, subfuzz_output=subfuzz_output, nmap_output=nmap_output)

    return render_template("recon.html")

if __name__ == "__main__":
    app.run(debug=True)
