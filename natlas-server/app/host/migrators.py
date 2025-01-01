import semver


def determine_data_version(hostdata):  # type: ignore[no-untyped-def]
    if "agent_version" in hostdata:
        ver = semver.VersionInfo.parse(hostdata["agent_version"])

        # 0.6.3 is our oldest host template set
        fallupVer = semver.VersionInfo.parse("0.6.3")

        # If agent_version is present and older than 0.6.3, "fall up" to 0.6.3 templates
        version = str(fallupVer) if ver < fallupVer else hostdata["agent_version"]
    else:
        version = str(fallupVer)  # type: ignore[used-before-def]

    return version
