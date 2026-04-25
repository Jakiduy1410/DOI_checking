Bit-Flip Error Resilience in LLMs:

A Comprehensive Analysis and Defense Framework

# Yuhang Chen1 Zhen Tan2 Ajay Jaiswal3 Huaizhi Qu1 Xinyu Zhao1 Qi Lin2 Yu Cheng4 Andrew Kwong1 Zhichao Cao2 Tianlong Chen1

1The University of North Carolina at Chapel Hill 2Arizona State University

3The University of Texas at Austin 4The Chinese University of Hong Kong

{yuhang, huaizhiq, xinyu, andrew, tianlong}@cs.unc.edu

{ztan36, qlin36, Zhichao.Cao}@asu.edu ajayjaiswal@utexas.edu chengyu05@gmail.com

# Abstract

Bit-flip errors (BFEs) are hardware faults where individual bits in memory or processing units are unintentionally flipped. These errors pose a significant threat to neural network reliabil- ity because even small changes in model pa- rameters can lead to large output shifts. Large language models (LLMs) are particularly vul- nerable to resource-constrained or outdated hardware. Such hardware often lacks error- correction mechanisms and faces aging issues, leading to instability under the vast parame- ter counts and heavy computational loads of LLMs. While the impact of BFEs on tradi- tional networks like CNNs is relatively well- studied, their effect on the complex archi- tecture of transformers remains largely unex- plored. *Firstly*, this paper presents a compre- hensive systematic analysis of BFE vulnera- bilities in key LLM components, revealing dis- tinct sensitivities across parameters, activations, and gradients during fine-tuning and inference. *Secondly*, based on our findings, we introduce a novel defense strategy *FlipGuard*: (***i***) exponent bit protection, and (***ii***) a self-correction based fine-tuning mechanism, to address BFE conse- quences. *FlipGuard* minimizes performance degradation while significantly enhancing ro- bustness against BFEs. Experiments demon- strate an average 9*.*27% reduction in accuracy drop under 1% BFEs on the SST-2 dataset us- ing BERT, and an average 36*.*35-point improve- ment in perplexity on the Wikitext-103 dataset using GPT-2, compared to unprotected mod- els. These results show the potential of our approach in enabling reliable LLM deployment on diverse and less reliable hardware platforms.

# Introduction

Bit-flip Errors (BFEs) are hardware faults where individual bits in memory or processing units (e.g., GPUs) are unintentionally flipped from 0 to 1 or vice versa, as shown in Figure [1](#_bookmark0). While often linked to **aging** or resource-constrained hardware, recent

![](data:image/png;base64...)![](data:image/jpeg;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/jpeg;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)

Aging Hardware Rowhammer Attack Large-scale Clusters

0100**0**0……01010 6.293799

**Bit-Flip Errors**

0100**1**0……01010 412468.5

*e.g.,* parameter value

Deploy

x = 15…happiness and joy, ensuring everyone finds the right answer.

Solve for x:

2x + 5 = 15 Collapse Output

Figure 1: Illustration of how BFEs occur and impact LLMs. BFEs change values in GPUs, altering binary representations (*e.g.*, flipping 1 bit, value shifts from 6.293799 to 412468.5), which causes collapse outputs.

studies highlight that even minimal bit manipula- tions can severely degrade LLM performance or create backdoors ([Liu et al.](#_bookmark37), [2024](#_bookmark37)), and BFEs in common LLM data formats like bfloat16 can cause up to 98% performance loss ([Lhoussaine et al.](#_bookmark33), [2024](#_bookmark33)).

LLMs, with their vast parameter scales ([Rad-](#_bookmark40) [ford](#_bookmark40), [2018](#_bookmark40); [Devlin](#_bookmark20), [2018](#_bookmark20)) and high computational demands ([Ajay Jain](#_bookmark15), [2024](#_bookmark15)), exacerbate this vul- nerability. Their deployment on diverse hardware, including older GPUs lacking robust error correc- tion or specialized units prioritizing speed over fault tolerance (e.g., for bfloat16 operations), in- creases BFE risk. This leads to **instability** from fre- quent memory operations, making BFE investiga- tion crucial for reliable LLM deployment. Besides, BFEs can also be intentionally induced by **attacks** such as Rowhammer ([Kim et al.](#_bookmark31), [2014](#_bookmark31)), which ex- ploits the increasing transistor density in DRAM, even in modern chips like DDR4 and DDR5 mem- ory technologies ([Frigo et al.](#_bookmark23), [2020](#_bookmark23); [Jattke et al.](#_bookmark29), [2024](#_bookmark29)). Moreover, the increasing reliance on *cloud infrastructure* for LLMs, particularly in large-scale clusters, amplifies this threat. The multi-tenant

10414

*Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing*, pages 10414–10424 November 4-9, 2025 ©2025 Association for Computational Linguistics

setup in public clouds, such as OpenAI’s use of Microsoft Azure, shares memory hardware among clients, raising the risk of Rowhammer attacks and BFEs due to extensive data processing and compu- tations ([Xiao et al.](#_bookmark49), [2016](#_bookmark49)). *Therefore*, investigating BFEs in LLMs is essential for ensuring their reli- ability and robustness in real-world environments where hardware limitations are common.

Previous research has extensively explored the impact of BFEs on traditional neural net- works, such as Convolutional Neural Networks (CNNs) ([Breier et al.](#_bookmark16), [2018](#_bookmark16)). In these networks, BFEs can lead to significant drops in accuracy. However, these networks typically have fewer pa- rameters and simpler architectures. In contrast, LLMs, with their massive parameter sizes and multi-layer structure, are prone to the propagation of errors. Despite this, the impact of BFEs on transformer-based LLMs remains under-explored. Given the increased vulnerability of LLMs due to their scale and complexity, we propose investigat- ing how different components respond to BFEs in both fine-tuning and inference stages. This leads to the **first** critical research question:

***RQ1***: *How do bit-flip errors affect LLMs, given their unique architecture and scale?*

While some defense mechanisms have been pro- posed for smaller models, they are optimized for simpler architectures and are not directly applica- ble to LLMs. The massive scale of LLMs, coupled with intricate components like self-attention layers, requires novel strategies for detecting and mitigat- ing BFEs. In addition, the diverse deployment environments for LLMs, including outdated hard- ware and potentially hostile cloud infrastructures, compounds the need for flexible solutions. This brings us to the **second** research question:

***RQ2:*** *How can we design effective strategies to mitigate BFEs in LLMs?*

To address [***RQ1***](#_bookmark1), we conduct a systematic anal- ysis of the impact of BFEs on key components of LLMs during both fine-tuning and inference (Sec- tion [3](#_bookmark3)). Specifically, we examine how BFEs affect critical modules, including ❶ self-attention layers,

❷ multi-layer perceptrons (MLPs), and ❸ embed-

ding layers. Our analysis also explores the influ- ence of bit-flips at different numerical positions, with a particular focus on the exponent’s highest bit. We experimentally illustrate that errors induced in

the most bit result in **disproportionately large** per- formance degradation due to its exponential effect on numerical values. Additionally, our study shows that different LLM components are subjected to **varying degrees of susceptibility** to BFEs. For example, embedding layers and layers closer to the input are more vulnerable because errors in these parts propagate throughout the network.

Based on the findings, for [***RQ2***](#_bookmark2), we propose a defense strategy: (***i***) enhanced quantization tech- niques to protect critical bits, and (***ii***) a self- correction based fine-tuning mechanism that ex- poses the model to random BFEs during fine- tuning, allowing it to learn corrective patterns. These strategies are designed to improve the robust- ness of LLMs against BFEs, improving reliable deployment across heterogeneous hardware envi- ronments, including outdated devices and cloud- based platforms susceptible to malicious attacks. We summarize our key contributions as follows:

* ***Error Investigation.*** We systematically analyze the impact of BFEs on key components of LLMs during fine-tuning and inference, providing a de- tailed understanding of how bit-flips at various stages affect LLMs performance.
* ***Defense Design.*** We propose a novel two- pronged defense strategy (*i.e.*, bit protection and self-correction mechanisms) to mitigate the ef- fects of BFEs on LLM capabilities.
* ***Experiment Validation.*** We validate *FlipGuard* through extensive experiments, demonstrating significant improvements in robustness against BFEs. For example, our techniques can achieve a 36.35-point improvement in perplexity on the Wikitext-103 dataset using GPT-2.

# Related Works

**Bit-flip Errors and Defense in Neural Networks**. Bit-flip attacks (BFAs) are closely related to bit-flip errors (BFEs), as both involve changes in bit values that can impact neural network performance ([He](#_bookmark26) [et al.](#_bookmark26), [2020](#_bookmark26)). BFAs focus on *deliberately* inducing bit flips through methods like Rowhammer to ex- ploit hardware vulnerabilities ([Kim et al.](#_bookmark31), [2014](#_bookmark31)). Attackers employ techniques such as Progressive Bit Search to identify and flip critical bits, effec- tively degrading model performance with minimal perturbations. In contrast, BFEs occur randomly and unintentionally due to hardware faults, often caused by factors such as frequent access or ag-

ing memory components ([Liu et al.](#_bookmark36), [2023](#_bookmark36)). While BFAs are an active area of research, the effects of BFEs in LLMs remain underexplored but pose a serious threat to model reliability on resource- constrained hardware.

Defenses against BFAs are categorized into two main approaches: fault tolerance and fault detection. Fault tolerance methods, including binarization-aware training, improve the model’s resilience to BFEs but often come at the cost of reduced accuracy or increased computational over- head ([He et al.](#_bookmark26), [2020](#_bookmark26)). RREC ([Liu et al.](#_bookmark35), [2022](#_bookmark35)) uses redundant error-correcting codes to prevent BFEs propagation. NeuroPots ([Liu et al.](#_bookmark36), [2023](#_bookmark36)) introduce honey neurons to attract and trap bit-flips. On the other hand, fault detection mechanisms monitor the system for bit-flips during runtime. Hardware-level defenses, such as SEC-DED ([Hamming](#_bookmark25), [1950](#_bookmark25)), can mitigate some attacks but remain susceptible to more advanced Rowhammer variants ([Kwong](#_bookmark32) [et al.](#_bookmark32), [2020](#_bookmark32)). WRecon ([Li et al.](#_bookmark34), [2020](#_bookmark34)) focused on recovering corrupted weights during inference by reconstructing weights affected by bit-flip errors. **Bit-flip Errors in LLMs**. LLMs are vulnerable to numerical corruptions ([Jiao et al.](#_bookmark30), [2024](#_bookmark30); [Mukher-](#_bookmark39) [jee et al.](#_bookmark39), [2003](#_bookmark39)). Although there has been exten- sive research on BFEs in CNNs ([Liu et al.](#_bookmark36), [2023](#_bookmark36); [He et al.](#_bookmark26), [2020](#_bookmark26)), the impact of bit-flip errors on LLMs remains unexplored. Meta has highlighted the importance of researching BFEs in LLMs ([Jiao](#_bookmark30) [et al.](#_bookmark30), [2024](#_bookmark30)). Given the increasing scale of LLMs and their deployment in diverse hardware environ- ments, it is crucial to investigate their vulnerability to BFEs, which is essential for ensuring the reliable deployment of LLMs in real-world applications.

# LLM Serving with Bit-flip Errors

## Bit-flip Error Setups

In this section, we define the BFEs simulation se- tups for LLMs. These errors arise naturally due to aging or resource-constrained hardware and oc- cur unpredictably. The random nature of BFEs can differently impact key components, leading to different consequences. We aim to simulate the

temporary incorrect outputs for a given prompt. A small amount of BFEs can potentially bring a dramatically different response.

* Fine-tuning BFEs: These BFEs may lead to per- manent degradation in the model’s learned pa- rameters, degrading future inference.

**Multi-Level Error Simulations**. We conduct tar- geted simulations to evaluate the impact of BFEs at multiple levels of the model:

* Model Parameters: We simulate BFEs across layers, focusing on embedding, attention, MLP, and LayerNorm layers to reveal whether BFEs affect different components differently.
* Activations: We analyze BFEs in activations at different stages of the model, exploring whether BFEs have different impacts on stages closer to the input versus those closer to the output.
* Gradients: We examine gradient-level BFEs’ im- pact during fine-tuning and the differences in BFE behavior between fine-tuning and inference.
* Bits Position: We simulate BFEs at different bit positions to identify which bit positions are more sensitive and critical to model stability.

## Multi-Level Bit-Flip Error Simulation

* + 1. **BFE Impact on Model Parameters**

**Observation 1** *BFEs in the parameter of the embedding layer have the most significant impact on the model’s performance.*

In transformer-based LLMs, bit-flip errors can impact various components, including the embed- ding, self-attention, MLP, and LayerNorm layers. BFEs can disrupt token representations and alter attention scores, leading to performance degrada- tion. This analysis helps us understand how errors in each layer differently affect model behavior.

Given a model with parameters *W* =

{*W* 1*, W* 2*, . . . , WL*}, where *Wl* are the parame- ters of the *l*-th layer. Each element *Wl* from layer *l* is a floating-point number with *Nf* -bit binary rep- resentation. The bit-flip error is introduced by flip- ping a randomly selected bit in the floating-point representation of *Wl*. For a randomly chosen bit

*i*

effects of BFEs through the components of LLMs.

**Error Properties**. We assume that BFEs randomly

position

*i*

*k* ∈ {0*,* 1*, . . . , Nf* − 1}, the bit-flip error

occur during fine-tuning or inference, affecting any bit of the stored or processed numerical data.

is injected using the following XOR operation:

*W*ˆ *l* = *Wl* ⊕ 2*k* (1)

*i* *i*

**Error Scenarios**. We define the following scenar- ios to simulate the occurrence of BFEs in LLMs:

* Inference-Time BFEs: These BFEs may lead to

where *W*ˆ *l* is the perturbed weight after BFE, and ⊕

denotes the XOR operation. This formula applies

*i*

BFE to the *k*-th bit of the binary representation.

100

Embedding Attention MLP

LayerNorm

90

Accuracy (%)

100

90

![](data:image/png;base64...)

BFE 0.1%

BFE 1%

BFE 5%

BFE 10%

Accuracy (%)

100

![](data:image/png;base64...)90

Accuracy (%)

80

70

60

0.1 1 5 10

BFE Rate (%)

80

70

60

In 1 2 3 4 5 6 7 8 9 10 11 12Out

Layers

80

70

60 0**1** 4 8 12 16 20 24 28 32

Bit Position

1. BFEs on parameters.
2. BFEs on activations.
3. BFEs on different bit position.

Figure 2: Performance degradation of GPT-2 on the SST-2 dataset under varying bit-flip error (BFE) rates. (a) illustrates the effect of BFEs on different model parameters (Embedding, Attention, MLP, and LayerNorm). (b) displays the accuracy changes when BFEs are applied to activations across different model layers. (c) shows the accuracy impact when BFEs are introduced at different bit positions within the model’s parameters.

Thus, the error-injected model parameter set is:

*W*ˆ = {*W*ˆ 1*, W*ˆ 2*, . . . , W*ˆ *L*} (2)

We experiment with GPT-2 on the SST-2 dataset to measure the impact of BFEs across four differ- ent layers. BFEs are simulated at rates of {0.1%, 1%, 5%, 10%} in each type of layer. Figure [2](#_bookmark4)(a) shows that BFEs in the embedding layer most sig- nificantly degrade performance. We argue this is because errors in embeddings propagate through the entire model. The attention and MLP layers exhibit moderate sensitivity, while LayerNorm is the least affected. These results highlight the im- portance of preserving embedding layer integrity to maintain model accuracy.

## BFE Impact on Activations

**Observation 2** *BFEs in activations near the input layer have more significant impact on model performance due to their larger cas- cading effect.*

In our analysis of how BFEs impact activations, we investigate errors introduced at different layers of the model: near the input, middle, and output. Activations represent the immediate output of a layer’s computation, defined as: *Al* = *f* (*WlAl*−1+ *bl*) where *Al* is the activation at layer *l*, *Wl* are the weights, *bl* are the biases, and *f* (·) is the activation function. A BFE in the activation matrix *Al* at position *i* is modeled as:

*A*ˆ*l* = *Al* ⊕ 2*k* (3)

In Figure [2](#_bookmark4)(b), we evaluate the impact of BFEs on activations using GPT-2 and the SST-2 dataset. We inject BFEs at various activation stages of the model. Errors in activations closer to the input layer have a cascading effect through subsequent layers, leading to widespread performance degra- dation. Conversely, errors in later activations have fewer impacts. This underscores the importance of detecting and mitigating errors in earlier activations to maintain model integrity.

## BFE Impact on Gradients

**Observation 3** *BFEs occurring in the fine- tuning stage will cause more long-term dam- age to model performance compared to inference-stage BFEs.*

|  |  |  |  |
| --- | --- | --- | --- |
| **BFE rate** | **FT-Grad.** | **FT-All** | **Infer.-All** |
| 0.1% | 77.34 | 75.12 | 81.31 |
| 1% | 71.88 | 69.89 | 75.61 |

Table 1: Accuracy results for different BFE rates on GPT-2 with SST-2 dataset under various experimental conditions. *FT-Grad.* refers to BFEs in gradients during fine-tuning, *FT-All* to BFEs in all values during fine- tuning, and *Infer.-All* to BFEs during inference.

Bit-flip errors during fine-tuning can have a far more detrimental effect than those occurring during inference. This is because BFEs in the fine-tuning stage can corrupt gradient updates, directly impact- ing model weights and leading to permanent perfor-

*i i* mance degradation. These corrupted updates can

where ⊕ is the XOR operation, and *k* is the bit position affected in the binary representation of the

activation value *Al*. This bit-flip error modifies the output of the layer and propagates forward:

*i*

*Al*+1 = *f* (*Wl*+1*A*ˆ*l* + *bl*+1) (4)

either amplify parameter changes or render them ineffective, causing unstable training, poor conver- gence, and a model that is more vulnerable to errors in future inference. As a result, fine-tuning BFEs poses a higher long-term risk to model robustness.

The results in Table [1](#_bookmark6) confirm this trend and *i* *i*

|  |  |  |  |
| --- | --- | --- | --- |
| |*Wl*| Range | Proportion | |*Wl*| Range | Proportion |
| (2−32*,* 2−8] | 3*.*106% | (2−2*,* 2−1] | 6*.*183% |
| (2−8*,* 2−4] | 37*.*09% | (2−1*,* 2] | 0*.*248% |
| (2−4*,* 2−2] | 53*.*38% | (2*,* +∞) | **0.0012%** |

illustrate that BFEs during fine-tuning, particu- larly when they corrupt gradients, have a more pronounced and lasting impact on model perfor-

*i,j*

mance than BFEs during inference.

## BFE Impact on Bit Positions

Table 2: Distribution of absolute parameter values for GPT-2 fine-tuned on the Wikitext-103 dataset. The proportion of |*Wl* | greater than 2 is extremely small

**Observation 4** *BFEs in the highest exponent bit lead to the most significant performance degradation due to the large magnitude shift they cause.*

Floating-point numbers in computing are typ- ically represented using the IEEE 754 standard. For an *N* -bit floating-point number *Wk*, the bits are divided into three components: Sign Bit (*S*): *b*1, Exponent Bits (*E*): *b*2*, b*3*, . . . , b*1+*e*, Mantissa (Fraction) Bits (*M* ): *b*2+*e, . . . , bN* . The floating- point value is calculated as:

*i*

*Wl* = (−1)*S* · 2*E*−*E*bias · (1 + *M* ) (5)

*i*

Where *E*bias = 2*e*−1 − 1. For 32-bit single- precision floating-point numbers, *S* is *b*1, *E* spans *b*2 to *b*9, and *M* spans *b*10 to *b*32. In our ex- periments shown as Table [2](#_bookmark7), 99.9988% of GPT- 2 parameters lie within [−(2 − 2−23)*,* 2 − 2−23], meaning the highest exponent bit, *b*2, is typically

0. When *b*2 = 0, the exponent *E* − *E*bias can

(1,445 of 124,439,808).

fine-tuning phase and mitigating the impact of BFEs in critical components of the model.

## Defense Design

**Self-Correction Fine-Tuning.** According to Ob- servation [3](#_bookmark5), BFEs during fine-tuning have a greater impact than those occurring during inference. This is because errors introduced during fine-tuning propagate into the learned parameters, leading to long-term degradation in the model. To ad- dress this, we propose a self-correction mechanism where the model is exposed to BFEs during fine- tuning, allowing it to learn to correct such errors.

We inject BFEs into the model during the fine- tuning phase. Let *θ* represent the original model parameters, and *θ*˜ represent the parameters after introducing BFEs. For each parameter *θi* in layer *l*, a randomly selected bit position *k* in its floating- point representation by XOR operation:

range from −127 to 0, constraining *Wl* within

*i,j*

*θ*˜*i* = *θi* ⊕ 2*k* (6)

[−2*,* 2]. Since the maximum mantissa value *M*max

is less than 1, even when other bits change, param- eters remain within [−2*,* 2] range. If *b*2 is flipped from 0 to 1, the exponent increases by 27, causing *E*′ = *E* + 128, which leads to extreme parameter

values. This dramatic increase causes *W*ˆ *l* to be-

*i*

come extremely large or small, risking overflow or

This bit-flip injection allows the model to simulate errors that occur during deployment, forcing it to correct them during training. The total loss func- tion Ltotal combines the standard task-specific loss

Ltask and a self-correction loss LSC, encouraging

the model to learn outputs resilient to BFEs:

L = Ltask(*θ*) + *λ*SCLSC(*θ*˜*, θ*)

instability. When lower exponent bits (e.g., *b*3) or mantissa bits flip, the changes are much smaller

LSC

(*θ*˜*, θ*) = E

*x*∼D

*ℓ fθ*˜(*x*)*, fθ*(*x*)

(7)

and parameters stay within a manageable range. Our experiments of GPT-2 on SST-2 in Figure [2](#_bookmark4)(c) show that flipping *b*2 from 0 to 1 leads to the most significant performance degradation, while errors in lower bits have minimal impact. This demon- strates the importance of preserving the highest exponent bit for model stability and robustness.

# Methodology

In this section, we introduce our defense strate- gies against bit-flip errors (BFEs) in large language models (LLMs), guided by the key observations from our analysis in Section [3](#_bookmark3). Our approach fo- cuses on enhancing model robustness during the

where the self-correction loss LSC is the divergence

between outputs with and without BFEs. *ℓ* denotes

*l*2-norm by default.

**Exponent Bit Protection.** Observation [4](#_bookmark8) shows that BFEs in the highest exponent bit of floating- point parameters result in drastic performance degradation. To prevent significant magnitude shifts, we mask the highest exponent bit and further constrain parameter values during training. Dur- ing inference, we modify the parameters to ensure the highest exponent bit remains 0. The corrected

parameter *θ*ˆ*i* is then given by:

*θ*ˆ*i* = *θi* & (1 ≪ (*N* − 2)) (8) Alternatively, to prevent parameters from reaching

**Algorithm 1:** FlipGuard

**Input :**Model parameters *θ*, dataset D, learning rate *η*, self-correction weight *λ*SC, BFE rate *ρ*

**for** *each epoch e* = 0*,* 1*, . . . , E* **do** Step 1: Randomly select *ρ* × |*θ*| parameters from *θ*;

**for** *each selected parameter θi* **do** Randomly select bit *k* and flip: *θ*˜*i* = *θi* ⊕ 2*k*;

Step 2: Compute task loss:

Ltask(*fθ*˜(*x*)*, y*);

and self-correction loss:

LSC = *ℓ*(*fθ*˜(*x*)*, fθ*(*x*)); Ltotal = Ltask + *λ*SCLSC; Step 3: Update parameters by *θ* → *θ* − *η*∇Ltotal;

Step 4: Apply exponent mask and clip:

*θ*ˆ*i* = clip(*θi,* −(2 − 2−*M* )*,* 2 − 2−*M* );

ing that errors remain bounded. Besides, our Self- Correction Fine-Tuning trains the model to mini- mize divergence between outputs with and without BFEs, further bounding the Lipschitz constant.

**Combination with LoRA and quantization.** Quantization reduces model size and cost by oper- ating at the weight and activation level, but BFEs still occur at the bit representation level in hard- ware. This distinction means BFEs can still occur post-quantization. While fewer bits in quantized models (e.g., 4-bit, 8-bit) reduce exponent-related perturbations, they may amplify BFE impact due to lower numerical precision. Our method, which self-corrects bit-level perturbations, remains fully compatible with other techniques. Combining it with LoRA ([Hu et al.](#_bookmark28), [2021](#_bookmark28)) and quantization en- hances computational efficiency while maintaining robustness to BFEs, enabling resource-efficient de- ployment in constrained environments. We further

discuss computational overhead in [5.3](#_bookmark11).

# Experiment

values that would set the highest exponent bit to 1, during fine-tuning, we clip the parameter values within a defined range [−*ϵ, ϵ*], where *ϵ* = 2 − 2−*M* and *M* denotes the number of mantissa bits, ensur- ing the highest exponent bit remains unaffected:

*θ*ˆ*i* = clip(*θi,* −*ϵ, ϵ*) (9) This range represents the safe interval within which the parameters can fluctuate without causing the most significant bit of the exponent to flip to 1. Thus, we avoid potential numerical instability or overflow issues that arise from range exceeding.

## Discussion

![](data:image/png;base64...)![](data:image/png;base64...)**Theoretical Analysis of BFEs and FlipGuard.** Sensitivity analysis are widely used to study the ro- bustness of neural networks by quantifying the rela- tionship between input or parameter perturbations and output stability. Previous works ([Virmaux and](#_bookmark46) [Scaman](#_bookmark46), [2018](#_bookmark46); [Chen et al.](#_bookmark17), [2024](#_bookmark17)) show that Lips- chitz continuity ensures bounded output changes for small input perturbations. Lipschitz constant

## Experimental Setup

**Models** We use four widely-used pre-trained Large Language Models in our experiments: BERT ([De-](#_bookmark20) [vlin](#_bookmark20), [2018](#_bookmark20)), GPT-2 Medium ([Radford et al.](#_bookmark41), [2019](#_bookmark41)), OpenLlama-3B ([Touvron et al.](#_bookmark45), [2023](#_bookmark45); [Geng and](#_bookmark24) [Liu](#_bookmark24), [2023](#_bookmark24)), Gemma 2-2B ([Team et al.](#_bookmark44), [2024](#_bookmark44)) and Llama 3.2-1B ([Dubey et al.](#_bookmark22), [2024](#_bookmark22)).

**Datasets**. We employ eight datasets across vari- ous NLP tasks to evaluate the impact of bit-flip errors on model performance: MRPC (paraphrase detection) ([Dolan and Brockett](#_bookmark21), [2005](#_bookmark21)), MNLI (nat- ural language inference) ([Williams et al.](#_bookmark48), [2017](#_bookmark48)), SST-2 (sentiment classification) ([Socher et al.](#_bookmark43), [2013](#_bookmark43)), CoLA (linguistic acceptability) ([Warstadt](#_bookmark47), [2019](#_bookmark47)), MMLU (multi-task language understand- ing) ([Hendrycks et al.](#_bookmark27), [2020](#_bookmark27)), ARC-E (science question answering) ([Clark et al.](#_bookmark18), [2018](#_bookmark18)), Wikitext- 103 (language modeling, text generation) ([Merity](#_bookmark38) [et al.](#_bookmark38), [2016](#_bookmark38)), SQuAD (question answering) ([Ra-](#_bookmark42) [jpurkar](#_bookmark42), [2016](#_bookmark42)), and GSM8K (math problem solv- ing) ([Cobbe et al.](#_bookmark19), [2021](#_bookmark19)).

is defined as *L* = sup

*x*1̸=*x*2

*f* (*x*1)−*f* (*x*2) , Such

![](data:image/png;base64...)![](data:image/png;base64...)1 2

*x* −*x*

**Metrics**. we report accuracy or F1-score for classi-

stable neural networks require small and bounded Lipschitz constant. However, bit-flip perturbations, especially in the highest exponent bit, can cause unbounded changes (e.g., up to 2128 for 32-bit FP value) which invalidates the utility of the Lips- chitz constant. Our Exponent Bit Protection con- strains parameters to a safe interval [−*ϵ, ϵ*], ensur-

fication tasks and perplexity for generation tasks. **Implementation Details**. All experiments were implemented using PyTorch, with models run- ning on two RTX 2080Ti GPUs. We used pre- trained models from HuggingFace. Fine-tuning was conducted with a learning rate of 5e-5 and batch sizes of 16 (classification) and 8 (genera-

|  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Model** | **Dataset** | **Clean** | **BFEs** | **SEC-DED** | **DHBFA** | **WRecon** | **RREC** | **NeuroPots** | **Ours** |
| **BERT** | MRPC ↑ | 87*.*64±2*.*29 | 70*.*27±2*.*24 | 73*.*95±2*.*12 | 62*.*74±2*.*26 | 72*.*19±2*.*53 | 73*.*51±2*.*13 | **76.18**±1*.*79 | 75*.*93±1*.*78 |
| MNLI ↑ | 84*.*32±0*.*74 | 68*.*73±0*.*95 | 71*.*92±0*.*81 | 66*.*89±0*.*99 | 63*.*27±1*.*35 | 69*.*45±0*.*66 | 72*.*16±0*.*85 | **78.12**±0*.*79 |
| SST-2 ↑ | 93*.*18±1*.*52 | 76*.*12±1*.*71 | 78*.*56±1*.*48 | 70*.*19±1*.*67 | 78*.*84±1*.*59 | 77*.*63±1*.*70 | 79*.*27±1*.*63 | **85.39**±1*.*54 |
| CoLA ↑ | 60*.*49±2*.*03 | 42*.*73±2*.*27 | 49*.*78±2*.*14 | 46*.*29±2*.*35 | 47*.*83±2*.*34 | 48*.*95±2*.*22 | 50*.*31±2*.*09 | **52.67**±2*.*05 |
| **GPT-2** | MMLU ↑ | 45*.*17±1*.*89 | 32*.*71±1*.*67 | 34*.*52±1*.*88 | 34*.*21±1*.*52 | 37*.*82±1*.*64 | 30*.*96±1*.*64 | 36*.*82±1*.*84 | **38.94**±1*.*44 |
| SST-2 ↑ | 92*.*73±1*.*46 | 75*.*61±1*.*65 | 76*.*52±1*.*59 | 71*.*32±1*.*76 | 74*.*51±1*.*82 | 77*.*35±1*.*73 | 79*.*12±1*.*81 | **80.58**±1*.*72 |
| ARC-E ↑ | 62*.*24±1*.*94 | 46*.*78±1*.*83 | 50*.*21±1*.*90 | 41*.*87±1*.*66 | 49*.*73±1*.*82 | 47*.*61±1*.*77 | 52*.*31±1*.*99 | **54.12**±1*.*71 |
| Wikitext-103 ↓ | 40*.*45±2*.*87 | 92*.*64±3*.*56 | 88*.*45±3*.*03 | 78*.*34±3*.*44 | 83*.*83±3*.*55 | 97*.*39±3*.*83 | 75*.*72±3*.*25 | **56.29**±3*.*11 |
| **Llama 1** | MNLI ↑ | 83*.*21±0*.*72 | 67*.*12±0*.*97 | 70*.*56±0*.*87 | 68*.*29±0*.*96 | 71*.*11±1*.*30 | 65*.*79±0*.*93 | 73*.*18±0*.*99 | **75.23**±0*.*73 |
| MMLU ↑ | 47*.*61±1*.*98 | 33*.*19±1*.*85 | 36*.*19±1*.*77 | 35*.*12±1*.*97 | 34*.*45±1*.*79 | 36*.*84±1*.*94 | 38*.*84±1*.*80 | **39.34**±1*.*84 |
| ARC-E ↑ | 61*.*13±1*.*12 | 45*.*79±1*.*90 | 49*.*18±1*.*14 | 48*.*26±1*.*52 | 50*.*31±1*.*34 | 47*.*23±2*.*20 | 52*.*49±1*.*01 | **53.94**±1*.*15 |
| Wikitext-103 ↓ | 22*.*89±2*.*20 | 55*.*94±3*.*09 | 43*.*61±2*.*53 | 49*.*82±2*.*8 | 55*.*23±2*.*60 | 52*.*34±3*.*20 | 44*.*91±2*.*50 | **40.62**±2*.*20 |
| **Gemma 2** | MRPC ↑ | 88*.*68±2*.*32 | 69*.*38±2*.*17 | 72*.*14±2*.*08 | 68*.*15±2*.*35 | 70*.*92±2*.*22 | 67*.*81±2*.*29 | **75.29**±2*.*24 | 73*.*88±1*.*81 |
| SST-2 ↑ | 91*.*23±1*.*89 | 74*.*58±1*.*98 | 76*.*79±1*.*95 | 75*.*23±1*.*95 | 72*.*84±1*.*81 | 77*.*64±1*.*96 | **80.17**±1*.*87 | 79*.*64±1*.*77 |
| ARC-E ↑ | 63*.*87±1*.*91 | 47*.*26±2*.*02 | 51*.*74±1*.*77 | 50*.*91±1*.*92 | 48*.*12±1*.*75 | 51*.*34±2*.*00 | 54*.*32±1*.*74 | **55.63**±1*.*69 |
| Wikitext-103 ↓ | 23*.*45±2*.*90 | 60*.*64±3*.*24 | 58*.*45±2*.*88 | 50*.*34±3*.*09 | 54*.*83±3*.*23 | 59*.*39±3*.*55 | 48*.*72±2*.*14 | **48.29**±2*.*94 |
| **Llama 3.2** | SQuAD ↑ | 86*.*17±1*.*12 | 67*.*84±1*.*31 | 72*.*91±1*.*25 | 69*.*83±1*.*20 | 74*.*23±1*.*16 | 75*.*92±1*.*29 | 74*.*15±1*.*28 | **78.35**±1*.*05 |
| GSM8K ↑ | 44*.*41±1*.*48 | 32*.*35±0*.*98 | 35*.*63±1*.*70 | 36*.*81±1*.*05 | 34*.*95±1*.*62 | 32*.*53±0*.*71 | 37*.*84±2*.*62 | **38.84**±1*.*50 |

Table 3: Performance comparison of models on corresponding datasets under various inference conditions: clean, with 1% BFEs, and using different defense methods. Accuracy is the evaluation metric for tasks {MRPC, MNLI, SST-2, CoLA, MMLU, ARC-E, GSM8K}, perplexity for task {Wikitext-103}, and F1-score for task {SQuAD}.

tion), across 5 epochs. Bit-flip errors were sim- ulated at various rates. Specifically, we simulate errors at 0*.*1%, 1%, 5%, and 10% of the model’s numerical representations during fine-tuning and inference by default. The code can be found at <https://github.com/UNITES-Lab/FlipGuard>. **Counterparts**. To validate the effectiveness of our proposed defense strategies, we compare them against several baseline and state-of-the-art meth-

ods designed to mitigate bit-flip errors:

* + - **SEC-DED** ([Hamming](#_bookmark25), [1950](#_bookmark25)): Single Error Cor- rection, Double Error Detection, a classic error correction technique for hardware fault tolerance.
    - **DHBFA** ([He et al.](#_bookmark26), [2020](#_bookmark26)): A defense against ad- versarial BFAs by leveraging binarization-aware training and piece-wise clustering.
    - **WRecon** ([Li et al.](#_bookmark34), [2020](#_bookmark34)): A method focused on recovering corrupted weights during inference by reconstructing weights affected by bit-flip errors.
    - **RREC** ([Liu et al.](#_bookmark35), [2022](#_bookmark35)): Uses redundant error- correcting codes to prevent BFEs propagation.
    - **NeuroPots** ([Liu et al.](#_bookmark36), [2023](#_bookmark36)): Introduce honey neurons to attract and trap bit-flips.

## Comparisons to State-of-the-Art

We compare accuracy and perplexity across all methods on clean data and under a 1% BFE rate, as shown in Table [3](#_bookmark10).

❶ **Impact of BFEs on Performance.** BFEs de- grade performance significantly across all models. For instance, BERT accuracy on MRPC drops from 87.64% to 70.27%, while Gemma 2’s perplexity on Wikitext-103 rises sharply from 23.45 to 60.64, highlighting the severity of BFE-induced errors.

❷ **Effectiveness of Defense Mechanisms.** De- fense methods mitigate BFE impact to varying ex- tents. For BERT on MRPC, our method improves accuracy from 70.27% to 75.93%, outperforming SEC-DED (73.95%) and approaching NeuroPots (76.18%). For Llama 1-3B on Wikitext-103, our defense reduces perplexity from 55.94 to 40.62, demonstrating strong error resilience.

* **Comparison of Defense Methods.** Across mod- els, our defense consistently achieves superior re- sults. For instance, in Llama 1-3B on MNLI, ac- curacy improves from 67.12% to 75.23%, surpass- ing other defenses and confirming its robustness against BFEs.

## Diagnostic Analysis

**Ablation Study on Defense Components.** We evaluate the impact of the two defense mechanisms through four configurations: (1) baseline (no de- fense), (2) self-correction fine-tuning, (3) exponent bit protection, and (4) their combination. Table [4](#_bookmark12) presents the results across BFE rates {0.1%, 1%,

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **SC EP** | **0.1%** | **1%** | **5%** | **10%** |
| ✗ ✗ | 81*.*31 | 75*.*61 | 66*.*31 | 60*.*81 |
| * ✗ | 82*.*44*↑*1*.*13 | 77*.*32*↑*1*.*71 | 72*.*12*↑*5*.*81 | 70*.*97*↑*10*.*16 |
| ✗ ✓ | 84*.*32*↑*3*.*01 | 78*.*34*↑*2*.*73 | 74*.*23*↑*7*.*92 | 71*.*56*↑*10*.*75 |
| ✓ ✓ | **85.92***↑*4*.*61 | **80.58***↑*4*.*97 | **76.56***↑*10*.*25 | **74.12***↑*13*.*31 |

|  |  |  |
| --- | --- | --- |
| **Component** | **w/o. Defense** | **w. Defense** |
| Embedding | 29*.*10 | **37.25***↑*8*.*15 |
| Self-Attention | 31*.*32 | **38.45***↑*7*.*13 |
| MLP | 39*.*20 | **39.90***↑*0*.*70 |
| LayerNorm | 43*.*10 | **43.50***↑*0*.*40 |

Table 4: **Ablation Study** on defense components under varying BFE rates for GPT-2 on the SST-2 dataset. BFE rates are set to {0.1%, 1%, 5%, 10%}. SC denotes Self- Correcting Fine-tuning and EP denotes Exponent Bit Protection in Section [4.](#_bookmark9)

Table 5: GPT-2 accuracy on the MMLU dataset un- der component-specific BFEs (1%), comparing perfor- mance with and without the proposed defense strategies.

the relative sensitivity of different components, as it simulates real-world hardware faults where all

100

80

Accuracy (%)

60

40

20

0

MRPC SST-2 ARC-E

![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)![](data:image/png;base64...)

BFEs Only

w. Defense

90

85

BFE 0.1%

BFE 1%

Accuracy (%)

80

75

70

0.01 0.05 0.1 0.5 1.0

parameters have the same probability of bit-flips. We further analyze the impact of fixed BFE *count*. Despite not having the largest parameter size, the embedding layer exhibits the most significant per- formance degradation, highlighting its vulnerabil-

(a) Different BFEs rates. (b) *λ*SC Sensitivity Analysis. Figure 3: (a) Performance of models under different bit-flip error rates {0.1%, 1%, 5%, and 10%}. We test BERT on MRPC, GPT-2 on SST-2, and Gemma 2 on ARC-E. (b) Sensitivity analysis assessing the impact of varying *λ*SC on model robustness and task accuracy.

5%, 10%}. While both defenses individually im- prove performance, the combined strategy consis- tently outperforms them, especially at higher BFE rates. For instance, at 10% BFEs, the combined defense achieves the highest accuracy of 74.12%. **Resilience to BFEs at Different Error Rates.** We evaluate model resilience to varying BFE rates ({0.1%, 1%, 5%, 10%}) on BERT (MRPC), GPT-2

(SST-2), and Gemma2 (ARC-E). Without defense, accuracy steadily drops, while our defense mecha- nisms significantly mitigate performance degrada- tion, especially at higher BFE rates.

**Hyper-parameter** *λ***SC Sensitivity Analysis.** We analyze the effect of the self-correction weight *λ*SC on model robustness. As shown in Figure [3](#_bookmark13), in- creasing *λ*SC improves resilience to BFEs, but ex- cessively high values risk overfitting to errors, re- ducing overall performance.

**Defense for Component-Specific BFEs.** Using GPT-2 on MMLU, we inject 1% BFEs into individ- ual components (embedding, self-attention, MLP, LayerNorm) and apply our defense strategies. Re- sults show our methods are effective across all components, with embedding and self-attention layers benefiting the most. Even for less vulnerable components like LayerNorm, our defenses improve stability, demonstrating robustness at both whole- network and component levels.

**Impact of Fixed BFEs *Count***. Using the same BFE *rate* across modules allows us to compare

ity. Table [6](#_bookmark14) confirms that the embedding layer remains the most sensitive.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **Component** | **1 Bit** | **10 Bits** | **100 Bits** | **1000 Bits** |
| Embedding | 92.67 | 92.02 | 90.56 | 88.34 |
| Attention | 92.73 | 92.12 | 91.67 | 90.45 |
| MLP | 92.73 | 92.52 | 92.40 | 92.23 |
| LayerNorm | 92.73 | 92.68 | 91.65 | 89.43 |

Table 6: Impact of fixed BFE count on GPT-2 model performance on the SST-2 dataset.

**Computational Overhead.** The primary computa- tional overhead of FlipGuard comes from comput- ing the self-correction loss, which requires outputs from both clean and perturbed parameters. This overhead scales linearly with model size. However, leveraging LoRA ([Hu et al.](#_bookmark28), [2021](#_bookmark28)) reduces this cost by enabling clean and perturbed outputs in a sin- gle forward pass, minimizing matrix multiplication overhead. Although separate activation function ap- plications (e.g., Softmax) are needed, their cost is negligible compared to the linear transformations. On SST-2 with GPT-2, FlipGuard with LoRA adds only 22% computational time compared to standard fine-tuning but improves performance by 4.97%.

# 6 Conclusion

In this paper, we systematically evaluated the ef- fects of bit-flip errors (BFEs) across multiple levels of large language models (LLMs), including model parameters, activations, gradients, and bit positions. Our simulations revealed distinct vulnerabilities in different components. To mitigate the impact of BFEs, we introduced a defense strategy that sig- nificantly improves LLM robustness. Our findings highlight the need for robust error-mitigation tech- niques to ensure the reliability of LLMs across diverse deployment environments.

**Acknowledgement.** This work is partially sup- ported by Amazon Research Award, Cisco Faculty Award, UNC Accelerating AI Awards, NAIRR Pi- lot Award, OpenAI Researcher Access Award, and Gemma Academic Program GCP Credit Award.

# Limitation Discussions & Future Work

While our study provides comprehensive insights into the impact of bit-flip errors on large language models and proposes effective defense mechanisms, several limitations remain that open avenues for future research.

First, our experiments primarily focus on popu- lar models, including BERT, GPT-2, Gemma, and Llama. While these models represent diverse trans- former architectures, LLMs vary significantly in their scale, training regimes, and specific optimiza- tions. Future work could extend our analysis to other LLMs, such as newer models like GPT-3, to verify the generalizability of our findings and defense mechanisms across different architectures and parameter scales.

Second, We evaluated our defense mechanisms under specific BFE rates {0.1%, 1%, 5%, and 10%}. However, real-world hardware-induced errors vary dynamically based on hardware age, workload, and environment. Future studies should simulate these dynamic conditions for a more com- prehensive understanding of model behavior and defense robustness.

Third, our current work focuses on post-training defense mechanisms. Investigating the applica- tion of these methods during training could pro- vide valuable insights into how training-time error simulations influence model robustness. While re- training large-scale LLMs from scratch remains computationally prohibitive for us, future work by organizations with access to extensive computa- tional resources could explore this avenue. Simu- lating bit-flip errors during training might act as a form of regularization, akin to dropout, potentially enhancing the resilience of models under perturbed conditions.

Lastly, the proposed defense mechanisms, espe- cially during fine-tuning, introduce computational overhead. This may limit practicality for time- sensitive applications. Optimizing these mecha- nisms to reduce runtime costs, possibly through lightweight quantization or hardware-level support, remains an important area for future research.

# Ethical Statement

Our research focuses on defending Large Language Models (LLMs) against bit-flip errors (BFEs) to enhance AI system reliability and security. While our findings could be misused to exploit hardware vulnerabilities, we present our methods responsibly, emphasizing countermeasures rather than attack de- tails. All experiments were conducted in controlled environments, without real user data and adhering strictly to ethical guidelines to ensure that our work supports the development of secure and trustworthy AI technologies.

# References

Pieter Abbeel Ajay Jain, Tianjun Zhang. 2024. Towards robust and scalable large language models. *EECS, University of California, Berkeley*.

Jakub Breier, Xiaolu Hou, Dirmanto Jap, Lei Ma, Shivam Bhasin, and Yang Liu. 2018. [Practical](https://doi.org/10.1145/3243734.3278519) [fault attack on deep neural networks](https://doi.org/10.1145/3243734.3278519). In *Proceed- ings of the 2018 ACM SIGSAC Conference on Com- puter and Communications Security*, CCS ’18, page 2204–2206, New York, NY, USA. Association for Computing Machinery.

Erh-Chung Chen, Pin-Yu Chen, I Chung, Che-Rung Lee, et al. 2024. Data-driven lipschitz continuity: A cost- effective approach to improve adversarial robustness. *arXiv preprint arXiv:2406.19622*.

Peter Clark, Isaac Cowhey, Oren Etzioni, Tushar Khot, Ashish Sabharwal, Carissa Schoenick, and Oyvind Tafjord. 2018. Think you have solved question an- swering? try arc, the ai2 reasoning challenge. *arXiv preprint arXiv:1803.05457*.

Karl Cobbe, Vineet Kosaraju, Mohammad Bavarian, Mark Chen, Heewoo Jun, Lukasz Kaiser, Matthias Plappert, Jerry Tworek, Jacob Hilton, Reiichiro Nakano, et al. 2021. Training verifiers to solve math word problems. *arXiv preprint arXiv:2110.14168*.

Jacob Devlin. 2018. Bert: Pre-training of deep bidi- rectional transformers for language understanding. *arXiv preprint arXiv:1810.04805*.

Bill Dolan and Chris Brockett. 2005. Automati- cally constructing a corpus of sentential paraphrases. In *Third international workshop on paraphrasing (IWP2005)*.

Abhimanyu Dubey, Abhinav Jauhri, Abhinav Pandey, Abhishek Kadian, Ahmad Al-Dahle, Aiesha Letman, Akhil Mathur, Alan Schelten, Amy Yang, Angela Fan, et al. 2024. The llama 3 herd of models. *arXiv preprint arXiv:2407.21783*.

Pietro Frigo, Emanuele Vannacc, Hasan Hassan, Vic- tor Van Der Veen, Onur Mutlu, Cristiano Giuffrida,

Herbert Bos, and Kaveh Razavi. 2020. Trrespass: Exploiting the many sides of target row refresh. In *2020 IEEE Symposium on Security and Privacy (SP)*, pages 747–762. IEEE.

Xinyang Geng and Hao Liu. 2023. Openllama: An open reproduction of llama. *URL: https://github. com/openlm-research/open\_llama*.

Richard W Hamming. 1950. Error detecting and error correcting codes. *The Bell system technical journal*, 29(2):147–160.

Zhezhi He, Adnan Siraj Rakin, Jingtao Li, Chaitali Chakrabarti, and Deliang Fan. 2020. Defending and harnessing the bit-flip based adversarial weight at- tack. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pages 14095–14103.

Dan Hendrycks, Collin Burns, Steven Basart, Andy Zou, Mantas Mazeika, Dawn Song, and Jacob Steinhardt. 2020. Measuring massive multitask language under- standing. *arXiv preprint arXiv:2009.03300*.

Edward J Hu, Yelong Shen, Phillip Wallis, Zeyuan Allen-Zhu, Yuanzhi Li, Shean Wang, Lu Wang, and Weizhu Chen. 2021. Lora: Low-rank adap- tation of large language models. *arXiv preprint arXiv:2106.09685*.

Patrick Jattke, Max Wipfli, Flavien Solt, Michele Marazzi, Matej Bölcskei, and Kaveh Razavi. 2024. Zenhammer: Rowhammer attacks on amd zen-based platforms. In *33rd USENIX Security Symposium (USENIX Security 2024)*.

Xun Jiao, Fred Lin, Harish D Dixit, Joel Coburn, Ab- hinav Pandey, Han Wang, Jianyu Huang, Venkat Ramesh, Wang Xu, Daniel Moore, et al. 2024. Pvf (parameter vulnerability factor): A quantita- tive metric measuring ai vulnerability and resilience against parameter corruptions. *arXiv preprint arXiv:2405.01741*.

Yoongu Kim, Ross Daly, Jeremie Kim, Chris Fallin, Ji Hye Lee, Donghyuk Lee, Chris Wilkerson, Konrad Lai, and Onur Mutlu. 2014. Flipping bits in memory without accessing them: An experimental study of dram disturbance errors. *ACM SIGARCH Computer Architecture News*, 42(3):361–372.

Andrew Kwong, Daniel Genkin, Daniel Gruss, and Yu- val Yarom. 2020. Rambleed: Reading bits in memory without accessing them. In *41st IEEE Symposium on Security and Privacy (S&P)*.

Salah Lhoussaine, Georgios Tziantzioulis, Michael B. Sullivan, Vilas Sridharan, Nathan DeBardeleben, Christian Engelmann, and Simranjit Singh. 2024. [A](https://arxiv.org/abs/2412.07192) [first look at bfloat16 soft-error resilience in large lan-](https://arxiv.org/abs/2412.07192) [guage models](https://arxiv.org/abs/2412.07192). *Preprint*, arXiv:2412.07192.

Jingtao Li, Adnan Siraj Rakin, Yan Xiong, Lian- gliang Chang, Zhezhi He, Deliang Fan, and Chaitali Chakrabarti. 2020. Defending bit-flip attack through

dnn weight reconstruction. In *2020 57th ACM/IEEE Design Automation Conference (DAC)*, pages 1–6. IEEE.

Liang Liu, Yanan Guo, Yueqiang Cheng, Youtao Zhang, and Jun Yang. 2022. Generating robust dnn with resistance to bit-flip based adversarial weight attack. *IEEE Transactions on Computers*, 72(2):401–413.

Qi Liu, Jieming Yin, Wujie Wen, Chengmo Yang, and Shi Sha. 2023. {NeuroPots}: Realtime proactive de- fense against {Bit-Flip} attacks in neural networks. In *32nd USENIX Security Symposium (USENIX Se-*

*curity 23)*, pages 6347–6364.

Ziyao Liu, Jinyuan Jia, Jiachen T. Wang, Wenbo Guo, Zhaofeng He, and Xinyang Zhang. 2024. [Bit-sponge:](https://arxiv.org/abs/2411.13757) [A bit-level attack and defense for large language mod-](https://arxiv.org/abs/2411.13757) [els](https://arxiv.org/abs/2411.13757). *Preprint*, arXiv:2411.13757.

Stephen Merity, Caiming Xiong, James Bradbury, and Richard Socher. 2016. Pointer sentinel mixture mod- els. *arXiv preprint arXiv:1609.07843*.

Shubhendu S Mukherjee, Christopher Weaver, Joel Emer, Steven K Reinhardt, and Todd Austin. 2003. A systematic methodology to compute the architectural vulnerability factors for a high-performance micro- processor. In *Proceedings. 36th Annual IEEE/ACM International Symposium on Microarchitecture, 2003. MICRO-36.*, pages 29–40. IEEE.

Alec Radford. 2018. Improving language understanding by generative pre-training.

Alec Radford, Jeffrey Wu, Rewon Child, David Luan, Dario Amodei, Ilya Sutskever, et al. 2019. Language models are unsupervised multitask learners. *OpenAI blog*, 1(8):9.

P Rajpurkar. 2016. Squad: 100,000+ questions for machine comprehension of text. *arXiv preprint arXiv:1606.05250*.

Richard Socher, Alex Perelygin, Jean Wu, Jason Chuang, Christopher D Manning, Andrew Y Ng, and Christopher Potts. 2013. Recursive deep models for semantic compositionality over a sentiment treebank. In *Proceedings of the 2013 conference on empiri- cal methods in natural language processing*, pages 1631–1642.

Gemma Team, Morgane Riviere, Shreya Pathak, Pier Giuseppe Sessa, Cassidy Hardin, Surya Bhupati- raju, Léonard Hussenot, Thomas Mesnard, Bobak Shahriari, Alexandre Ramé, et al. 2024. Gemma 2: Improving open language models at a practical size. *arXiv preprint arXiv:2408.00118*.

Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. 2023. Llama: Open and effi- cient foundation language models. *arXiv preprint arXiv:2302.13971*.

Aladin Virmaux and Kevin Scaman. 2018. Lipschitz regularity of deep neural networks: analysis and ef- ficient estimation. *Advances in Neural Information Processing Systems*, 31.

A Warstadt. 2019. Neural network acceptability judg- ments. *arXiv preprint arXiv:1805.12471*.

Adina Williams, Nikita Nangia, and Samuel R Bow- man. 2017. A broad-coverage challenge corpus for sentence understanding through inference. *arXiv preprint arXiv:1704.05426*.

Yuan Xiao, Xiaokuan Zhang, Yinqian Zhang, and Radu Teodorescu. 2016. One bit flips, one cloud flops:{Cross-VM} row hammer attacks and privi- lege escalation. In *25th USENIX security symposium (USENIX Security 16)*, pages 19–35.