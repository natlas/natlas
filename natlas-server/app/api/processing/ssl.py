def parse_alt_names(cert_data):
    altnames = []
    # Parse out Subject Alternative Names because libnmap doesn't give them to us
    for line in cert_data.split("\n"):
        if line.startswith("Subject Alternative Name:"):
            for item in line.split(" ")[3:]:
                altname = item.strip(",").split("DNS:")
                if len(altname) > 1:  # Prevent an indexerror in edge case
                    altnames.append(altname[1])
    return altnames


def parse_subject(subject, altnames):
    subDict = {}
    if subject.get("commonName"):
        subDict["commonName"] = subject.get("commonName")
    if altnames:
        subDict["altNames"] = altnames
    return subDict


def parse_pubkey(pubkey):
    pubkeyDict = {}
    if pubkey.get("type"):
        pubkeyDict["type"] = pubkey.get("type")
    if pubkey.get("bits"):
        pubkeyDict["bits"] = int(pubkey.get("bits"))
    return pubkeyDict


def parse_ssl_data(sslcert):
    altnames = parse_alt_names(sslcert["output"])
    elements = sslcert["elements"]
    subject = elements.get("subject")
    issuer = elements.get("issuer")
    pubkey = elements.get("pubkey")
    sig_alg = elements.get("sig_algo")
    validity = elements.get("validity")
    md5 = elements.get("md5")
    sha1 = elements.get("sha1")
    pem = elements.get("pem")

    result = {}
    if subject:
        result["subject"] = parse_subject(subject, altnames)

    if issuer:
        result["issuer"] = issuer

    if pubkey:
        result["pubkey"] = parse_pubkey(pubkey)

    if sig_alg:
        result["sig_alg"] = sig_alg

    if validity:
        if validity.get("notAfter"):
            result["notAfter"] = validity.get("notAfter")
        if validity.get("notBefore"):
            result["notBefore"] = validity.get("notBefore")
    if md5:
        result["md5"] = md5
    if sha1:
        result["sha1"] = sha1
    if pem:
        result["pem"] = pem

    return result
