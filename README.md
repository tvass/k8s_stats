# k8s_stat

Fetch Kubernetes quotas from each namespaces and print related stats.
tvass / UQAM

```
Example : ./k8s_stat.py --kubeconfig="/path/to/kubeconfig" --filter=siad

    --kubeconfig : Default value set to "~/.kube/config".
    --filter : Namespaces starts with "string" (ie: siad). Don't use for NO filter.
    --debug : Print debug info
```

In our case, there is 1 quota per NS, named "quota-namespace".
Adapt code for your needs.

```
$ ./k8s_stat.py
Stats (79 namespaces with quota):

TOTAL CPU Request (core) ........ 22.22 (40%)
TOTAL CPU Limit   (core) ........ 192.5 (344%)
TOTAL MEM Request (Mi) .......... 50134.0 (35%)
TOTAL MEM Limit   (Mi) .......... 186992.0 (130%)
```
