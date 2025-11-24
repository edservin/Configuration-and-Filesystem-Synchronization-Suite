<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->

<a id="readme-top"></a>

<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

Contributors
Forks
Stargazers
Issues
MIT License
[LinkedIn][linkedin-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/[edservin]/Configuration-and-Filesystem-Synchronization-Suite">
    <!-- Replace with your project's logo if available -->
    <img src="https://raw.githubusercontent.com/othneildrew/Best-README-Template/master/images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">ASR5500 Configuration and Filesystem Synchronization Suite

</h3>

  <p align="center">
    Automate configuration saving, boot priority updates, and filesystem synchronization on Cisco ASR5500 devices.
    <br />
    <a href="https://github.com/[edservin]/Configuration-and-Filesystem-Synchronization-Suite"><strong>Explore the Repo »</strong></a>
    <br />
    <br />
    <a href="https://github.com/[edservin]/Configuration-and-Filesystem-Synchronization-Suite/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/[edservin]/Configuration-and-Filesystem-Synchronization-Suite/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#important-considerations">Important Considerations</a></li>
    <li><a href="#troubleshooting">Troubleshooting</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
About The Project

This Python script automates critical management tasks on Cisco ASR5500 devices, including saving the current configuration, updating the boot priority (boot system priority), and synchronizing the filesystem. It is designed to be executed before or after a planned change, ensuring devices boot with the correct configuration and maintain consistency. It uses concurrent processing to interact with multiple devices simultaneously, optimizing execution time.

Features

    Concurrent Automation: Processes multiple ASR5500 devices in parallel using ThreadPoolExecutor for fast and efficient execution.
    Excel-based Device Management: Reads device connection details (hostname, IP, credentials) from an Excel file.
    Configuration Saving: Saves the device's current configuration to flash memory with a descriptive filename that includes the hostname, date, change moment (BEFORE/AFTER), and change number.
    Dynamic Boot Priority Determination: Analyzes show boot output to identify the lowest existing boot priority.
    boot system priority Update: Configures a new boot system priority entry with a priority lower than the lowest existing one, pointing to the current boot image and the saved configuration.
    Essential Commands: Executes autoconfirm and filesystem synchronize all to ensure persistence of changes and filesystem integrity.
    Detailed HTML Report: Generates a comprehensive HTML report with the status of each device, key command outputs (final show boot, filesystem synchronize all), and any errors encountered.
    Extensive Logging: Records all operations, successes, warnings, and errors in a log file (asr_automation.log) for easy debugging and auditing.


<p align="right">(<a href="#readme-top">back to top</a>)</p>


Built With

    Python
    Pandas
    Netmiko
    Openpyxl


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
Getting Started

To get a local copy up and running follow these simple example steps.

Prerequisites

Ensure you have the following installed:

    Python 3.x (version 3.6 or higher recommended).
    SSH access to the ASR5500 devices from the machine where the script is run.
    Access credentials (username and password) with sufficient privileges to execute the necessary commands on the ASR5500s.


Installation

    Clone the repository (or download the script):
    bash
    Copy Code

    git clone https://github.com/[edservin]/Configuration-and-Filesystem-Synchronization-Suite.git
    cd Configuration-and-Filesystem-Synchronization-Suite

    Install Python dependencies:
    bash
    Copy Code

    pip install pandas netmiko openpyxl


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
Usage

The script is executed from the command line and requires three arguments: the change moment, the change number, and the path to the Excel file.

Input File Format

The Excel file (.xlsx) must contain a sheet with the following columns (column names must match exactly):

hostname 	ip 	username 	password
ASR-CORE-01 	10.1.1.1 	admin 	cisco123
ASR-EDGE-02 	10.1.1.2 	admin 	cisco123
... 	... 	... 	...

Script Execution

bash


Copy Code

python asr_config_saver.py <MOMENT> <CHG_NUMBER> <EXCEL_FILE_PATH>


Arguments:

    <MOMENT>: Indicates the moment of the change. Can be BEFORE or AFTER.
    <CHG_NUMBER>: The change number associated with the operation (e.g., CHG0001234).
    <EXCEL_FILE_PATH>: The full path to the Excel file containing the list of devices.


Example:

bash


Copy Code

python asr_config_saver.py BEFORE CHG0009876 /home/user/devices.xlsx


Output

Upon completion, the script will generate the following files:

    reporte_asr_YYYYMMDD_CHGXXXXXX.html: A detailed HTML report summarizing the status of each device, including key command outputs and any errors. The filename will include the date and change number.
    asr_automation.log: A log file containing a chronological record of all operations, informational messages, warnings, and errors. It is crucial for debugging.


Additionally, the console will display real-time progress messages.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


Important Considerations

    Credentials Security: For production environments, storing credentials directly in plain text within an input file is not recommended. Consider implementing a more secure method, such as environment variables, a secret management system, or prompting for credentials at runtime.
    delay_factor: The delay_factor values in the script are tuned for optimal performance. If you frequently experience NetmikoTimeoutException, especially for commands like filesystem synchronize all, consider slightly increasing the delay_factor for that specific command in the script.
    Concurrency (max_workers): The number of concurrent threads (max_workers) is set to 10 by default. You can adjust this value in the script if your machine or network has limitations, or if you wish to process more devices simultaneously.
    Network Connectivity: Ensure stable network connectivity to all target devices throughout the script's execution.


<p align="right">(<a href="#readme-top">back to top</a>)</p>


Troubleshooting

    "Error: El archivo Excel no se encontró." (Error: The Excel file was not found.): Verify the path and name of the Excel file.
    "Error al leer el archivo Excel..." (Error reading the Excel file...): Ensure the Excel file is not corrupted and that the columns match the expected format.
    NetmikoTimeoutException:
        Check network reachability (e.g., ping) to the device's IP address.
        Ensure that the SSH port (22) is open on the device and not blocked by a firewall.
        Consider increasing the delay_factor for the command causing the timeout in the script.
    NetmikoAuthenticationException: Double-check the username and password provided in the Excel file.
    Unexpected errors: Review the asr_automation.log file for specific exception details.


<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTRIBUTING -->
Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

    Fork the Project
    Create your Feature Branch (git checkout -b feature/AmazingFeature)
    Commit your Changes (git commit -m 'Add some AmazingFeature')
    Push to the Branch (git push origin feature/AmazingFeature)
    Open a Pull Request


Top contributors:

<a href="https://github.com/[edservin]/Configuration-and-Filesystem-Synchronization-Suite/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=[edservin]/Configuration-and-Filesystem-Synchronization-Suite" alt="contrib.rocks image" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
Contact

[Eduardo Servin] - [edservin@cisco.com]

Project Link: https://github.com/[edservin]/Configuration-and-Filesystem-Synchronization-Suite

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[linkedin-url]: https://linkedin.com/in/your-linkedin-profile # Replace with your LinkedIn profile URL
