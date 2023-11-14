# Gather details about Mirrorbits instances in the wild

Run as such:

```
./run.py mirrorbits.yaml
```

It can be useful to do a run for only one instance, eg:

```
./run.py -i gimp mirrorbits.yaml
```

To also get the number of files on the mirror, we need to enable the rsync
listing. Since it takes a while to run, we'd better also save the complete
output into a directory:

```
./run.py -i gimp -o out --rsync mirrorbits.yaml
```

There are more settings available, but not exposed via the command-line, so
have a look at the script and modify what needs be.
