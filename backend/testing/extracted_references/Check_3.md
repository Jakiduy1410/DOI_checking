1. “PyTorch,” https://github*.*com/pytorch/pytorch.
2. S. C. Yin Ho, V. Majdinasab, M. Islam, D. E. Costa, E. Shihab,

F. Khomh, S. Nadi, and M. Raza, “An empirical study on bugs inside pytorch: A replication study,” in 2023 IEEE International Conference on Software Maintenance and Evolution (ICSME), 2023, pp. 220–231.

1. J. Chen, Y. Liang, Q. Shen, J. Jiang, and S. Li, “Toward understanding deep learning framework bugs,” 2023.
2. T. Makkouk, D. J. Kim, and T.-H. P. Chen, “An empirical study on per- formance bugs in deep learning frameworks,” in 2022 IEEE International Conference on Software Maintenance and Evolution (ICSME), 2022, pp. 35–46.
3. L. Jia, H. Zhong, X. Wang, L. Huang, and X. Lu, “The symptoms, causes, and repairs of bugs inside a deep learning library,” Journal of Systems and Software, vol. 177, p. 110935, 2021. [Online]. Available: [https://www*.*sciencedirect*.*com/science/article/pii/S0164121221000327](http://www.sciencedirect.com/science/article/pii/S0164121221000327)
4. Y. Yang, T. He, Z. Xia, and Y. Feng, “A comprehensive empirical study on bug characteristics of deep learning frameworks,” Information and Software Technology, vol. 151, p. 107004, 2022. [Online]. Available: [https://www*.*sciencedirect*.*com/science/article/pii/S0950584922001306](http://www.sciencedirect.com/science/article/pii/S0950584922001306)
5. M. M. Morovati, A. Nikanjam, F. Tambon, F. Khomh, and Z. M. J. Jiang, “Bug characterization in machine learning-based systems,” Empirical Software Engineering, vol. 29, no. 1, p. 14, Dec 2023.

[Online]. Available: https://doi*.*org/10*.*1007/s10664-023-10400-0

1. X. Du, Y. Sui, Z. Liu, and J. Ai, “An empirical study of fault triggers in deep learning frameworks,” IEEE Transactions on Dependable and Secure Computing, vol. 20, no. 4, pp. 2696–2712, 2023.
2. F. Tambon, A. Nikanjam, L. An, F. Khomh, and G. Antoniol, “Silent bugs in deep learning frameworks: an empirical study of keras and tensorflow,” Empirical Software Engineering, vol. 29, no. 1, p. 10, Nov 2023. [Online]. Available: https://doi*.*org/10*.*1007/s10664-023-10389-6
3. Q. Guo, X. Xie, Y. Li, X. Zhang, Y. Liu, X. Li, and C. Shen, “Audee: automated testing for deep learning frameworks,” in Proceedings of the 35th IEEE/ACM International Conference on Automated Software Engineering, ser. ASE ’20. New York, NY, USA: Association for Computing Machinery, 2021, p. 486–498. [Online]. Available: https://doi*.*org/10*.*1145/3324884*.*3416571
4. M. Li, J. Cao, Y. Tian, T. O. Li, M. Wen, and S.-C. Cheung, “Comet: Coverage-guided model generation for deep learning library testing,” 2023.
5. A. H. Phan, P. Tichavsky´, and A. Cichocki, “On fast computation of gradients for candecomp/parafac algorithms,” 2012. [Online]. Available: https://arxiv*.*org/abs/1204*.*1586
6. C.-H. Chu, K. S. Khorassani, Q. Zhou, H. Subramoni, and D. K. Panda, “Dynamic kernel fusion for bulk non-contiguous data transfer on gpu clusters,” in 2020 IEEE International Conference on Cluster Computing (CLUSTER). IEEE, 2020, pp. 130–141.
7. K. K. Suresh, K. S. Khorassani, C. C. Chen, B. Ramesh, M. Abdul- jabbar, A. Shafi, H. Subramoni, and D. K. Panda, “Network assisted non-contiguous transfers for gpu-aware mpi libraries,” in 2022 IEEE Symposium on High-Performance Interconnects (HOTI). IEEE, 2022,

pp. 13–20.

1. D. K. Pal and M. Savvides, “Learning non-parametric invariances from data with permanent random connectomes,” CoRR, vol. abs/1911.05266, 2019. [Online]. Available: [http://arxiv*.*org/abs/1911*.*05266](http://arxiv.org/abs/1911.05266)
2. W. Wu, G. Bosilca, R. Vandevaart, S. Jeaugey, and J. Dongarra, “Gpu- aware non-contiguous data movement in open mpi,” in Proceedings of the 25th ACM International Symposium on High-Performance Parallel and Distributed Computing, 2016, pp. 231–242.
3. M. Osama, S. D. Porumbescu, and J. D. Owens, “A programming model for gpu load balancing,” in Proceedings of the 28th ACM SIGPLAN Annual Symposium on Principles and Practice of Parallel Programming, 2023, pp. 79–91.
4. D.-L. Lin and T.-W. Huang, “Efficient gpu computation using task graph parallelism.” Springer, Cham, 2021, pp. 435–450.
5. D. A. Matthews, “High-performance tensor contraction without trans- position,” 2016.
6. C. Guo, R. Zhang, J. Xu, J. Leng, Z. Liu, Z. Huang, M. Guo, H. Wu,

S. Zhao, J. Zhao, and K. Zhang, “Gmlake: Efficient and transparent gpu memory defragmentation for large-scale dnn training with virtual memory stitching,” in Proceedings of the 29th ACM International Conference on Architectural Support for Programming Languages and Operating Systems, Volume 2, ser. ASPLOS ’24. New York, NY, USA: Association for Computing Machinery, 2024, p. 450–466. [Online]. Available: https://doi*.*org/10*.*1145/3620665*.*3640423

1. “linalg.householder product is incorrect when given non-contiguous inputs 67513,” https://github*.*com/pytorch/pytorch/issues/67513.
2. “Incorrect gradient for masked select when inputs are non-contiguous ,” https://github*.*com/pytorch/pytorch/issues/99638.
3. “kthvalue incorrect with strided GPU tensor ,” https://github*.*com/ pytorch/pytorch/issues/45721.
4. “Custom Autograd Functions Don’t Work If Forward Pass Outputs a List of Tensors ,” https://github*.*com/pytorch/pytorch/issues/87713.
5. “Investigate from padded implementations correctness,” https://github*.*com/pytorch/pytorch/issues/84082.
6. “Investigate from padded implementations correctness,” https://github*.*com/pytorch/pytorch/issues/84082.
7. “Calling nested tensor.transpose(-1, -2) causes autograd error,”

://github.com/pytorch/pytorch/issues/94303.

1. “Calling saved tensors hooks. exit inside unpack hook can lead to segfault,” https://github*.*com/pytorch/pytorch/issues/130734.
2. “Segmentation fault when a Tensor backward hook removes itself,” https://github*.*com/pytorch/pytorch/issues/58354.
3. “Segmentation fault in dataloader after upgrading to pytorch v1.8.0 53894,” https://github*.*com/pytorch/pytorch/issues/53894.
4. “SSegfault on setting gradient value to instance of user-defined class 64813,” https://github*.*com/pytorch/pytorch/issues/64813.
5. “CUDA error: an illegal memory access was encountered when us- ing output padding in nn.ConvTranspose3d 32866,” https://github*.*com/ pytorch/pytorch/issues/32866.
6. “Illegal Memory Access was encountered in AvgPool2d CUDA kernel 84018,” https://github*.*com/pytorch/pytorch/issues/84018.
7. “Cross Entropy doesn’t work with the specific batch, but works with each sample from this batch 108345,” https://github*.*com/pytorch/pytorch/ issues/108345.
8. “Incorrect and inconsistent outputs from CrossEntropy- Loss(reduction=”none”) with torch.float16 dtype 111484,” https://github*.*com/pytorch/pytorch/issues/111484.
9. “Wrong output of single-channel channels last convolution with channels first input 82060,” hhttps://github*.*com/pytorch/pytorch/issues/82060.
10. “[PT2.0] Channels last for weight for ConvTranpose gives Random output 99519,” https://github*.*com/pytorch/pytorch/issues/99519.
11. “CUDA native batch norm backward returns non-channels last grad for channels last input 107199,” https://github*.*com/pytorch/pytorch/issues/ 107199.
12. “Segment Fault after model inference all images using C++ API,” https:

//github*.*com/pytorch/pytorch/issues/38385.

1. “TORCH.UTILS.DATA,” https://pytorch*.*org/docs/master/data*.*html.
2. “NotImplementedError: Cannot access storage of SparseCsrTensorImpl 115330,” https://github*.*com/pytorch/pytorch/issues/115330.
3. “Calling pin memory() fails for nested tensor 102167,” https:// github*.*com/pytorch/pytorch/issues/102167.
4. “contiguous non-contiguous tensors,” https://github*.*com/pytorch/pytorch/issues/94303.
5. “Incorrect gradient for masked select when inputs are non-contiguous 99638,” https://github*.*com/pytorch/pytorch/issues/99638.
6. “call contiguous on BMM inputs for NT on CUDA 88108,” https:// github*.*com/pytorch/pytorch/pull/88108.
7. “[Breaking change 2.1] Passing non-contiguous inputs to SDPA on CUDA device with the mem-efficient attention backend returns garbage 112577,” https://github*.*com/pytorch/pytorch/issues/112577.
8. “Incorrect and inconsistent outputs from CrossEntropy- Loss(reduction=”none”) with torch.float16 dtype 111484,” https://github*.*com/pytorch/pytorch/issues/111484.
9. “[CUDA] 64-bit indexing fixes for cross-entropy kernels,” https:// github*.*com/pytorch/pytorch/pull/112096.
10. “sparse.mm produces incorrect derivatives 102493,” https://github*.*com/ pytorch/pytorch/issues/102493.
11. “sparse.mm.backward: fix for non-contiguous grad values on CPU 106127,” https://github*.*com/pytorch/pytorch/pull/106127.
12. “[NestedTensor] Add a contiguous checks to get buffer 86496,” https:

//github*.*com/pytorch/pytorch/pull/86496.

1. “Custom Autograd Functions Don’t Work If Forward Pass Outputs a List of Tensors 87713,” https://github*.*com/pytorch/pytorch/issues/87713.
2. “torch.flip not implemented for non-contiguous boolean tensors 52062,” https://github*.*com/pytorch/pytorch/issues/52062.
3. “sparse.mm.backward: fix for non-contiguous grad values on CPU,” https://github*.*com/pytorch/pytorch/pull/106127.
4. “[Breaking change 2.1] Passing non-contiguous inputs to SDPA on CUDA device with the mem-efficient attention backend returns garbage,” https://github*.*com/pytorch/pytorch/issues/112577.
5. “Pull Request #86496: Fix for contiguous tensor handling in PyTorch,” https://github*.*com/pytorch/pytorch/pull/86496.
6. “Contigious vs non-contigious tensor,” https://discuss*.*pytorch*.*org/t/

contigious-vs-non-contigious-tensor/30107/2.

1. “Performance of contiguous vs. non-contiguous tensors,” https://discuss*.*pytorch*.*org/t/performance-of-contiguous-vs-non- contiguous-tensors/107288.
2. “Different between permute, transpose, view? Which should I use?” https://discuss*.*pytorch*.*org/t/different-between-permute-transpose-view- which-should-i-use/32916.
3. “what makes a tensor have non-contiguous memory?” https://stackoverflow*.*com/questions/54095351/in-pytorch-what-makes- a-tensor-have-non-contiguous-memory.
4. “What does .contiguous() do in PyTorch?” https://stackoverflow*.*com/ questions/48915810/what-does-contiguous-do-in-pytorch.
5. “What’s the difference between ‘reshape()‘ and ‘view()‘ in PyTorch?” https://stackoverflow*.*com/questions/49643225/whats-the-difference- between-reshape-and-view-in-pytorch/49644300#49644300.
6. “Incorrect and inconsistent outputs from CrossEntropy- Loss(reduction=”none”) with torch.float16 dtype,” https:

//github*.*com/pytorch/pytorch/issues/111484.

1. “Cross Entropy doesn’t work with the specific batch, but works with each sample from this batch,” https://github*.*com/pytorch/pytorch/issues/ 108345.
2. “BF16 Matmul not get same result on cuda and cpu,” https://github*.*com/ pytorch/pytorch/issues/111457.
3. “OpenACC: cuStreamSynchronize crash when using pointers as parameters,” https://forums*.*developer*.*nvidia*.*com/t/openacc- custreamsynchronize-crash-when-using-pointers-as-parameters/ 196944.
4. M. Bauer, H. Cook, and B. Khailany, “Cudadma: optimizing gpu memory bandwidth via warp specialization,” in Proceedings of 2011 international conference for high performance computing, networking, storage and analysis, 2011, pp. 1–11.
5. “efficiency of copying a strided array,” https:// forums*.*developer*.*nvidia*.*com/t/efficiency-of-copying-a-strided-array/ 135518.
6. “Efficient Host-Device Data Transfer,” https://engineering*.*purdue*.*edu/

∼smidkiff/ece563/NVidiaGPUTeachingToolkit/Mod14DataXfer/

Mod14DataXfer*.*pdf.

1. “How to transfer massive data efficiently?” https:// forums*.*developer*.*nvidia*.*com/t/how-to-transfer-massive-data- efficiently/37621.
2. “Why is the transfer throughput low when transferring small size data from Host to Device (or Device to Host)?” https://forums*.*developer*.*nvidia*.*com/t/why-is-the-transfer-throughput- low-when-transferring-small-size-data-from-host-to-device-or-device- to-host/153962.
3. “2 same Quadro P1000 cards, but only one can install Ubuntu.” https://forums*.*developer*.*nvidia*.*com/t/2-same-quadro-p1000-cards-but- only-one-can-install-ubuntu/64612.
4. “Memory read error when using csrmv with transpose oper- ation,” https://forums*.*developer*.*nvidia*.*com/t/memory-read-error-when- using-csrmv-with-transpose-operation/136019/8.
5. “CUDA C++ Programming Guide,” https://docs*.*nvidia*.*com/cuda/cuda- c-programming-guide/index*.*html.
6. “ Memory Management,” https://docs*.*nvidia*.*com/cuda/cuda-runtime- api/groupCUDARTMEMORY*.*html.