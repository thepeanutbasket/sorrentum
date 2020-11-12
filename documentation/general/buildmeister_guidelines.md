<!--ts-->
   * [General](#general)
   * [Notification system](#notification-system)
   * [Buildmeister instructions](#buildmeister-instructions)
   * [Post-mortem analysis](#post-mortem-analysis)
<!--te-->

# General

- Buildmeister rotates every 2 weeks
  - To see who is the Buildmeister now refer to
    [Buildmeister spreadsheet "Buildmeister rotation"](https://docs.google.com/spreadsheets/d/1AajgLnRQka9-W8mKOkobg8QOzaEVOnIMlDi8wWVATeA/edit#gid=0),
- Buildmeister is responsible for:
  - Pushing team members to fix broken tests
  - Conducting post-mortem analysis, see
    [Buildmeister spreadsheet, "Post-mortem breaks analysis"](https://docs.google.com/spreadsheets/d/1AajgLnRQka9-W8mKOkobg8QOzaEVOnIMlDi8wWVATeA/edit#gid=1363431255),

- Testing workflows are available via
  [github actions](https://github.com/ParticleDev/commodity_research/tree/master/documentation_p1/general/github_actions.md):
  - The fast tests workflow is triggered every 2 hours
  - The slow tests workflow is triggered every 4 hours
  - The super-slow tests workflow is to be implemented
  - Additional information about the
    [tests](https://github.com/alphamatic/amp/blob/master/documentation/general/unit_tests.md#running-unit-tests)

- Historical notes
  - This document was generated from the
    [gdoc](https://docs.google.com/document/d/1lrLIU5XYs8hIGlvpZWWjo73-TZTug86vAtvJLRpvfeQ/edit?usp=sharing)
    using the [markdown extension](https://github.com/evbacher/gd2md-html/wiki)
  - The gdoc is superseded by this document

# Notification system

- `@p1_GH_bot` notifies the team about breaks via Telegram channel `@ALL`
- A notification contains:
  - Failing tests type: fast/slow/super-slow
  - Link to a failing run
  - Example:
    ```python
    Build failure 'Fast tests'.
    https://github.com/ParticleDev/commodity_research/actions/runs/248816321
    ```

# Buildmeister instructions

- You receive a break notification from `@p1_GH_bot`
- Have a look at the message
  - Do it right away, this is always your highest priority task
- Notify the team
  - Post on the `@ALL` Telegram channel what tests broke, e.g.,
    ```python
    FAILED knowledge_graph/vendors/p1/test/test_p1_utils.py::TestClean::test_clean
    FAILED knowledge_graph/vendors/nbsc/test/test_nbsc_utils.py::TestExposeNBSCMetadata::test_expose_nbsc_metadata
    ```
  - Ask if somebody knows what is the problem
    - If you know who is in charge of that test (you can use `git blame`) ask
      directly
  - If the offender says that it's fixing the bug right away, let he / she do it
  - Otherwise file a bug to track the issue

- File an Issue in ZH to report the failing tests and the errors
  - Issue title template `Build fail (test type) (run number)`
    - Example: `Build fail fast_tests (987074894)`
  - Paste the URL of a failing run
    - Example: https://github.com/ParticleDev/commodity_research/runs/987074894
  - Provide as much information as possible to give an understanding of the
    problem
    - List all the tests with FAILED status in a github run
      ```python
      FAILED knowledge_graph/vendors/p1/test/test_p1_utils.py::TestClean::test_clean
      FAILED knowledge_graph/vendors/nbsc/test/test_nbsc_utils.py::TestExposeNBSCMetadata::test_expose_nbsc_metadata
      ```
    - Stack trace or part of it (if it's too large)
      ```python
      Traceback (most recent call last):
      File "/commodity_research/automl/hypotheses/test/test_rh_generator.py", line 104, in test1
        kg_metadata, _ = p1ut.load_release(version="0.5.2")
      File "/commodity_research/knowledge_graph/vendors/p1/utils.py", line 53, in load_release
        % version,
      File "/commodity_research/amp/helpers/dbg.py", line 335, in dassert_dir_exists
        _dfatal(txt, msg, *args)
      File "/commodity_research/amp/helpers/dbg.py", line 97, in _dfatal
        dfatal(dfatal_txt)
      File "/commodity_research/amp/helpers/dbg.py", line 48, in dfatal
        raise assertion_type(ret)
      AssertionError:
      ################################################################################
      * Failed assertion *
      dir='/fsx/research/data/kg/releases/timeseries_db/v0.5.2' doesn't exist or it's not a dir
      The requested version 0.5.2 has no directory associated with it.
      ```
  - Add the issue to the
    [BUILD - Breaks](https://app.zenhub.com/workspaces/particle-one-5e4448e6b9975964dfe1582f/issues/particledev/commodity_research/1564)
    Epic so that we can track it
  - If the failures are not connected to each other, file separate issues for
    each of the potential root cause
  - Keep issues grouped according to the codebase organization

- Post the issue reference on Telegram channel @ALL
  - You can quickly discuss there who will take care of the broken tests, assign
    that person
  - You can use `git blame` to see who wrote the test
  - Otherwise, assign it to the person who can reroute (e.g., Paul, GP, Sergey)

- Our policy is "fix it or revert"
  - The build needs to go back to green within 1 hr
    - Either the person responsible for the break fixes the bug within one hour
    - Or you need to push the responsible person to disable the test
    - Do not make the decision about disabling the test yourself!
      - First, check with the responsible person, and if he / she is ok with
        disabling, do it.
  - NB! Disabling the test is not the first choice, it's a measure of last
    resort!

- Regularly check issues that belong to the Epic
  [BUILD - Breaks](https://app.zenhub.com/workspaces/particle-one-5e4448e6b9975964dfe1582f/issues/particledev/commodity_research/1564).
  - You have to update the break issues if the problem was solved or partially
    solved.
  - Pay special attention to the failures which resulted in disabling tests

# Post-mortem analysis

- We want to understand on why builds are broken so that we can improve the
  system to make it more robust
  - In order to do that, we need to understand the failure modes of the system
  - For this reason we keep a log of all the issues and what was the root cause

- After each break fill the
  [Buildmeister spreadsheet sheet "Post-mortem breaks analysis"](https://docs.google.com/spreadsheets/d/1AajgLnRQka9-W8mKOkobg8QOzaEVOnIMlDi8wWVATeA/edit#gid=1363431255),
- `Date` column:
  - Enter the date when the break took place
  - Keep the bug ordered in reverse chronological order (i.e., most recent dates
    first)
- `Repo` column:
  - Specify the repo where break occurred
    - `amp`
    - `commodity_research`
- `Test type` column:
  - Specify the type of the failing tests
    - Fast
    - Slow
    - Super-slow
- `Link` column:
  - Provide a link to a failing run
- `Reason` column:
  - Specify the reason of the break
    - Merged a branch with broken tests
    - Master was not merged in a branch
    - Merged broken slow tests without knowing that
- `Issue` column:
  - Provide the link to the ZH issue with the break description
- `Solution` column:
  - Provide the solution description of the problem
    - Problem that led to the break was solved
    - Failing tests were disabled, i.e. problem was not solved