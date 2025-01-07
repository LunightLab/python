import os
import zipfile
import subprocess
from pathlib import Path

def calculate_folder_size(folder_path):
    """Calculate the total size of a folder, including its subfolders and files."""
    total_size = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
    return total_size

def calculate_embedded_library_sizes(libraries):
    """Calculate the sizes of the libraries listed by otool."""
    total_size = 0
    library_sizes = []

    for lib in libraries:
        lib_path = Path(lib)
        if lib_path.exists() and lib_path.is_file():
            size = lib_path.stat().st_size
            library_sizes.append({"name": lib, "size": size})
            total_size += size

    return total_size, library_sizes

def resolve_library_path(lib_path, app_folder):
    """Resolve the real path of a library given its dynamic path."""
    if lib_path.startswith("@rpath") or lib_path.startswith("@executable_path"):
        # Resolve dynamic paths relative to the app folder
        real_path = lib_path.replace("@rpath", str(app_folder / "Frameworks"))
        real_path = real_path.replace("@executable_path", str(app_folder))
        resolved_path = Path(real_path)
        return resolved_path if resolved_path.exists() else None
    elif Path(lib_path).exists():
        # Absolute path or already resolved path
        return Path(lib_path)
    return None

def find_libraries_in_mach_o(app_executable_path):
    """Use otool to find libraries embedded in the Mach-O executable and calculate sizes."""
    try:
        result = subprocess.run(
            ["otool", "-L", app_executable_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print(f"Error analyzing {app_executable_path}: {result.stderr}")
            return {"libraries": [], "executable_size": 0, "embedded_size": 0}

        libraries = []
        total_embedded_size = 0

        app_folder = app_executable_path.parent  # Resolve paths relative to the app folder

        for line in result.stdout.splitlines()[1:]:
            lib_path = line.strip().split(" ")[0]
            resolved_path = resolve_library_path(lib_path, app_folder)
            if resolved_path and resolved_path.exists():
                lib_size = resolved_path.stat().st_size
                total_embedded_size += lib_size
                libraries.append({"name": str(resolved_path), "size": lib_size})
            else:
                libraries.append({"name": lib_path, "size": 0})  # Unresolved paths

        executable_size = os.path.getsize(app_executable_path)

        return {
            "libraries": libraries,
            "executable_size": executable_size,
            "embedded_size": total_embedded_size
        }
    except FileNotFoundError:
        print("Error: otool is not installed or not found in PATH.")
        return {"libraries": [], "executable_size": 0, "embedded_size": 0}


def analyze_ipa_structure(extract_to, ipa_path):
    """Analyze the extracted IPA structure and report file sizes."""
    payload_path = Path(extract_to) / "Payload"
    structure_report = {
        "frameworks": [],
        "libraries": [],
        "embedded_libraries": [],
        "executable_size": 0,
        "embedded_size": 0,
        "resources_total_size": 0,
        "others": [],
        "ipa_size": 0,  # IPA 파일 크기
        "payload_size": 0,  # Payload 크기
        "download_size": 0  # 다운로드 크기 추정
    }

    # Calculate IPA file size
    ipa_size = os.path.getsize(ipa_path)
    structure_report["ipa_size"] = ipa_size

    # Estimate download size (60% of IPA size)
    structure_report["download_size"] = int(ipa_size * 0.6)

    if not payload_path.exists():
        print(f"Error: Payload directory not found in {extract_to}.")
        return None

    app_folder = next(payload_path.glob("*.app"), None)
    if not app_folder:
        print("Error: .app directory not found in Payload.")
        return None

    print(f"App Directory Found: {app_folder}")

    # Calculate Payload total size
    structure_report["payload_size"] = calculate_folder_size(payload_path)

    # Analyze Frameworks
    frameworks_dir = app_folder / "Frameworks"
    if frameworks_dir.exists():
        for framework in frameworks_dir.iterdir():
            if framework.is_dir():
                size = calculate_folder_size(framework)
                structure_report["frameworks"].append(
                    {"name": framework.name, "size": size}
                )
            elif framework.is_file():
                size = framework.stat().st_size
                structure_report["frameworks"].append(
                    {"name": framework.name, "size": size}
                )

    # Search for Libraries and calculate resources size
    total_resources_size = 0
    for root, dirs, files in os.walk(app_folder):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix in [".dylib", ".so"]:
                size = file_path.stat().st_size
                structure_report["libraries"].append({"name": file_path.name, "size": size})
            elif file_path.suffix in [".png", ".jpg", ".jpeg", ".json", ".plist", ".nib", ".svg", ".ttf"]:
                size = file_path.stat().st_size
                total_resources_size += size
            elif file_path.is_file():
                size = file_path.stat().st_size
                structure_report["others"].append({"name": file_path.name, "size": size})

    # Store total resources size
    structure_report["resources_total_size"] = total_resources_size

    # Analyze embedded libraries in the Mach-O executable
    app_executable = app_folder / app_folder.stem
    if app_executable.exists():
        embedded_info = find_libraries_in_mach_o(app_executable)
        structure_report["embedded_libraries"].extend(embedded_info["libraries"])
        structure_report["executable_size"] = embedded_info["executable_size"]
        structure_report["embedded_size"] = embedded_info.get("embedded_size", 0)

    return structure_report

def format_size(size_in_bytes):
    """Format file size into human-readable MB or KB."""
    if size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.2f} KB"
    return f"{size_in_bytes / (1024 * 1024):.2f} MB"


def export_to_txt(structure_report, output_path="analysis_report.txt"):
    """Export the analysis report to a TXT file."""
    def format_size(size_in_bytes):
        """Format file size into human-readable MB or KB."""
        if size_in_bytes < 1024 * 1024:
            return f"{size_in_bytes / 1024:.2f} KB"
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"

    with open(output_path, "w") as txt_file:
        txt_file.write("IPA Analysis Report\n")
        txt_file.write("=====================\n\n")
        txt_file.write("IPA Size(아카이브 된 앱사이즈):\n")
        txt_file.write(f"  - {format_size(structure_report['ipa_size'])}\n\n")
        txt_file.write("Estimated Download Size (App Store Optimized):\n")
        txt_file.write("앱스토어에서 다운로드되는 추정사이즈(payload사이즈의 70~80%)\n")
        txt_file.write(f"  - {format_size(structure_report['download_size'])}\n\n")
        txt_file.write("Payload Size (단말기에 실제 설치되는 사이즈)(Uncompressed):\n")
        txt_file.write(f"  - {format_size(structure_report['payload_size'])}\n\n")
        txt_file.write("Frameworks:\n")
        for framework in structure_report["frameworks"]:
            txt_file.write(f"  - {framework['name']}: {format_size(framework['size'])}\n")
        txt_file.write("\nLibraries:\n")
        if structure_report["libraries"]:
            for lib in structure_report["libraries"]:
                txt_file.write(f"  - {lib['name']}: {format_size(lib['size'])}\n")
        else:
            txt_file.write("  - No libraries found.\n")
        txt_file.write("\nResources Total Size:\n")
        txt_file.write(f"  - {format_size(structure_report['resources_total_size'])}\n\n")
        txt_file.write("Embedded Libraries:\n")
        for lib in structure_report["embedded_libraries"]:
            txt_file.write(f"  - {lib['name']}: {format_size(lib['size'])}\n")
        txt_file.write("\nExecutable Size:\n")
        txt_file.write(f"  - {format_size(structure_report['executable_size'])}\n\n")
        txt_file.write("Embedded Libraries Total Size:\n")
        txt_file.write(f"  - {format_size(structure_report['embedded_size'])}\n")
    print(f"TXT report saved to {output_path}")
    
def export_to_markdown(structure_report, output_path="analysis_report.md"):
    """Export the analysis report to a Markdown file."""
    with open(output_path, "w") as md_file:
        md_file.write("# IPA Analysis Report\n\n")
        md_file.write("## IPA Size(아카이브 된 앱사이즈)\n")
        md_file.write(f"- {format_size(structure_report['ipa_size'])}\n\n")
        md_file.write("## Estimated Download Size (App Store Optimized)\n")
        md_file.write("## 앱스토어에서 다운로드되는 추정사이즈(payload사이즈의 70~80%)\n")
        md_file.write(f"- {format_size(structure_report['download_size'])}\n\n")
        md_file.write("## Payload Size (단말기에 실제 설치되는 사이즈)(Uncompressed)\n")
        md_file.write(f"- {format_size(structure_report['payload_size'])}\n\n")
        md_file.write("## Frameworks\n")
        for framework in structure_report["frameworks"]:
            md_file.write(f"- {framework['name']}: {format_size(framework['size'])}\n")
        md_file.write("\n## Libraries\n")
        if structure_report["libraries"]:
            for lib in structure_report["libraries"]:
                md_file.write(f"- {lib['name']}: {format_size(lib['size'])}\n")
        else:
            md_file.write("- No libraries found.\n")
        md_file.write("\n## Resources Total Size\n")
        md_file.write(f"- {format_size(structure_report['resources_total_size'])}\n\n")
        md_file.write("## Embedded Libraries\n")
        for lib in structure_report["embedded_libraries"]:
            md_file.write(f"- {lib['name']}: {format_size(lib['size'])}\n")
        md_file.write("\n## Executable Size\n")
        md_file.write(f"- {format_size(structure_report['executable_size'])}\n\n")
        md_file.write("## Embedded Libraries Total Size\n")
        md_file.write(f"- {format_size(structure_report['embedded_size'])}\n")


def format_report(structure_report):
    """Format the structure report for display and export to files."""

    print("\nIPA Analysis Report:")
    print("=====================")

    print("\nIPA Size(아카이브 된 앱사이즈):")
    print(f"  - {format_size(structure_report['ipa_size'])}")

    print("\nEstimated Download Size (App Store Optimized):")
    print("앱스토어에서 다운로드되는 추정사이즈(payload사이즈의 70~80%)")
    print(f"  - {format_size(structure_report['download_size'])}")

    print("\nPayload Size (단말기에 실제 설치되는 사이즈)(Uncompressed):")
    print(f"  - {format_size(structure_report['payload_size'])}")

    print("\nFrameworks:")
    for framework in structure_report["frameworks"]:
        print(f"  - {framework['name']}: {format_size(framework['size'])}")

    print("\nLibraries:")
    if structure_report["libraries"]:
        for lib in structure_report["libraries"]:
            print(f"  - {lib['name']}: {format_size(lib['size'])}")
    else:
        print("  - No libraries found.")

    print("\nResources Total Size:")
    print(f"  - {format_size(structure_report['resources_total_size'])}")

    print("\nEmbedded Libraries:")
    for lib in structure_report["embedded_libraries"]:
        print(f"  - {lib['name']}: {format_size(lib['size'])}")

    print("\nExecutable Size:")
    print(f"  - {format_size(structure_report['executable_size'])}")

    print("\nEmbedded Libraries Total Size:")
    print(f"  - {format_size(structure_report['embedded_size'])}")

    # Export results to Markdown
    export_to_markdown(structure_report, "analysis_report.md")
    print("Markdown report saved: analysis_report.md")

    # Export results to TXT
    export_to_txt(structure_report, "analysis_report.txt")
    print("TXT report saved: analysis_report.txt")

def main():
    # 명령어 인자를 처리
    if len(os.sys.argv) < 2:
        print("Usage: python analyze_ipa.py <ipa_file> [<txt_file>] [<md_file>]")
        os.sys.exit(1)

    ipa_file = os.sys.argv[1]
    txt_file = os.sys.argv[2] if len(os.sys.argv) > 2 else "analysis_report.txt"
    md_file = os.sys.argv[3] if len(os.sys.argv) > 3 else "analysis_report.md"

    if not os.path.exists(ipa_file):
        print(f"Error: File {ipa_file} does not exist.")
        os.sys.exit(1)

    extract_to = "extracted_ipa"
    if os.path.exists(extract_to):
        os.system(f"rm -rf {extract_to}")

    print(f"Extracting IPA file: {ipa_file}")
    with zipfile.ZipFile(ipa_file, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    print("Analyzing IPA structure...")
    structure_report = analyze_ipa_structure(extract_to, ipa_file)

    if structure_report:
        format_report(structure_report)  # 화면에 리포트 출력
        export_to_markdown(structure_report, md_file)  # Markdown 파일 저장
        print(f"Markdown report saved: {md_file}")
        export_to_txt(structure_report, txt_file)  # TXT 파일 저장
        print(f"TXT report saved: {txt_file}")

if __name__ == "__main__":
    main()