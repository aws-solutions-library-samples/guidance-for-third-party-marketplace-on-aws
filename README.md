## Third-Party Marketplace Solutions for Retailers

Retailers want to offer a wide range of products to their customers but can't necessarily take on the cost of holding the inventory. For many, creating an online marketplace for thrid-party sellers addresses this problem and creates and additional revenue stream through listing fees. Customers, in turn, find more products they want and tend to spend more, creating a virtuous cycle that benefits the retailer, the third-party sellers, and the customers. 

## Reference Architecture

1. Supplier registration
2. Supplier approval process
3. New product registration
4. New product approval process
5. Updating inventory
6. Executing third party sale
7. Marketing insights
8. Data governance and lifecycle


## Welcome to your CDK Python project!

This CDK project with Python generates the AWS stack corresponding to the Third Party Marketplace guidance.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

