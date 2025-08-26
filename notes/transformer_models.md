### Transformer Model with Attention Mechanism

A transformer-based model can be represented as:

$$
R(L(R(LR(L....R(L(A(E(v)))))...)))
$$

Where:
- $E(v)$ maps input tokens to embeddings.
- $A$ is the attention mechanism, which can be expanded as:

$$
A(E(v)) = \sum_{h} \text{softmax} \left( \frac{Q_h K_h^T}{\sqrt{d_k}} \right) V_h
$$

Here:
- $h$ denotes different attention heads.
- $Q_h, K_h, V_h$ are query, key, and value matrices computed from embeddings.
- $d_k$ is a scaling factor to stabilize gradients.
- Softmax ensures proper weight distribution across token interactions.

Thus, the final recursive transformation applies multiple layers of attention and feedforward neural networks to obtain contextualized representations.

### Transformer Model with Residual Connections and Layer Normalization

A transformer-based model can be represented as:

$$
R(\text{LN}(L(R(\text{LN}(L R(\text{LN}(L....R(\text{LN}(L(A(E(v))) + E(v)))))...) + A(E(v))))))
$$

Where:
- $\text{LN}(\cdot)$ represents **Layer Normalization**, applied before each transformation.
- **Residual connections** add back the input to each sub-layer:
  - **Self-attention residual**: $A(E(v)) + E(v)$
  - **Feedforward residual**: $L(\text{LN}(A(E(v)) + E(v))) + \text{LN}(A(E(v)) + E(v))$

With this extended notation, we now have a complete representation of a transformer’s core components, including the stabilizing effects of layer normalization and residual connections.

### Next token prediction

A transformer-based language model can be represented as:

$$
R(\text{LN}(L(R(\text{LN}(L R(\text{LN}(L....R(\text{LN}(L(A(E(v_t))) + E(v_t)))))...) + A(E(v_t))))))
$$

where $v_t$ is the input token at timestep $t$, and the model iterates recursively to generate the next token:

$$
v_{t+1} = \text{argmax} ( \text{softmax} (L_{\text{final}}(R(\text{LN}(L(A(E(v_t))) + E(v_t))))) )
$$

### Learned Matrices in Training

During training, the model learns:
1. **Embedding matrix** $E$: Mapping discrete tokens to dense representations.
2. **Query, Key, and Value matrices** $Q, K, V$: Used in attention layers, obtained from training.
3. **Weight matrices** $L$: Linear transformation matrices in each layer.
4. **Final projection matrix** $L_{\text{final}}$: Used to transform the last hidden state into a probability distribution over the vocabulary.

Each learned parameter $\theta$ (e.g., $E, Q, K, V, L$) is updated using **gradient descent**:

To illustrate how gradient descent works, let each layer transformation follows:
$$ h_{\ell} = R(\text{LN}(L h_{\ell-1})) + h_{\ell-1} $$
where $h_{\ell}$ represents the hidden state at layer $\ell$.

To train the model, each parameter $\theta$ (e.g., $E, Q, K, V, L$) is updated via gradient descent using:
$$ \theta \leftarrow \theta - \eta \frac{\partial \mathcal{L}}{\partial \theta} $$
where:
- $\mathcal{L}$ is the loss function (typically cross-entropy loss for next-token prediction).
- $\frac{\partial \mathcal{L}}{\partial \theta}$ is the gradient, i.e the change of the loss function with respect to each parameter.
- $\eta$ is the learning rate.
The gradient propagates backward through each layer using the chain rule, ensuring earlier layers receive updates based on their contribution to the final loss:
$$ \frac{\partial \mathcal{L}}{\partial h_{\ell}} = \frac{\partial \mathcal{L}}{\partial h_{\ell+1}} \frac{\partial h_{\ell+1}}{\partial h_{\ell}} $$
where:
- The final layer outputs gradients to all previous layers recursively.
- Each weight matrix $L_{\ell}$ is adjusted using:
$$ L_{\ell} \leftarrow L_{\ell} - \eta \frac{\partial \mathcal{L}}{\partial L_{\ell}} $$
Similarly, attention weights $Q, K, V$ are updated by propagating gradients back through their computation:
$$ Q_h \leftarrow Q_h - \eta \frac{\partial \mathcal{L}}{\partial Q_h}, \quad K_h \leftarrow K_h - \eta \frac{\partial \mathcal{L}}{\partial K_h}, \quad V_h \leftarrow V_h - \eta \frac{\partial \mathcal{L}}{\partial V_h} $$
