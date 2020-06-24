import semver


def determine_data_version(hostdata):
    if "agent_version" in hostdata:
        ver = semver.VersionInfo.parse(hostdata["agent_version"])

        # 0.6.3 is our oldest host template set
        fallupVer = semver.VersionInfo.parse("0.6.3")

        # If agent_version is present and older than 0.6.3, "fall up" to 0.6.3 templates
        if ver < fallupVer:
            version = str(fallupVer)
        else:
            version = hostdata["agent_version"]
    else:
        version = str(fallupVer)

    return version
