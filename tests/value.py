import trimesh
import kaolin
from torchsdf import index_vertices_by_faces, compute_sdf
import os
import torch

os.environ["CUDA_VISIBLE_DIVICES"] = "1"
device = "cuda"
# Ns
num_sample = 1000000

all_pass = True

print("====Value test====")
for model in os.listdir("tests/models"):
    print("Test:", model[:-4], end=" ")
    model_path = os.path.join("tests/models", model)
    mesh = trimesh.load(model_path, force="mesh", process=False)
    samples = torch.rand((num_sample, 3)).to(device)
    # (Ns, 3)
    x = samples.clone().requires_grad_()
    # (Nv, 3)
    verts = torch.Tensor(mesh.vertices.copy()).to(device)
    # (Nf, 3)
    faces = torch.Tensor(mesh.faces.copy()).long().to(device)
    # (1, Nf, 3, 3)
    face_verts = kaolin.ops.mesh.index_vertices_by_faces(
        verts.unsqueeze(0), faces)
    # (Nf, 3, 3)
    face_verts_ts = index_vertices_by_faces(verts, faces)

    # Kaolin
    # (1, Ns)
    distances, face_indexes, types = kaolin.metrics.trianglemesh.point_to_mesh_distance(
        x.unsqueeze(0), face_verts)
    gradient = torch.autograd.grad([distances.sum()], [x], create_graph=True,
                                   retain_graph=True)[0]

    # TorchSDF
    # (Ns)
    distances_ts, face_indexes_ts, types_ts = compute_sdf(x, face_verts_ts)
    gradient_ts = torch.autograd.grad([distances_ts.sum()], [x], create_graph=True,
                                      retain_graph=True)[0]
    dis_fit = torch.allclose(distances, distances_ts)
    grad_fit = torch.allclose(gradient, gradient_ts)
    if (dis_fit and grad_fit):
        print("\x1B[32mPass\x1B[0m")
    else:
        all_pass = False
        if (not dis_fit):
            print("\x1B[31mDistance wrong!\x1B[0m")
        if (not grad_fit):
            print("\x1B[31mGradient wrong!\x1B[0m")

if (all_pass):
    print("====\x1B[32mAll pass\x1B[0m====")
else:
    print("====\x1B[31mWrong\x1B[0m====")