import { useState } from 'react';
import { FolderKanban, Plus, Users, FileText, Calendar, MessageSquare, ChevronRight } from 'lucide-react';
import type { UserMode } from '../App';

interface ProjectsPageProps {
  userMode: UserMode;
}

interface Project {
  id: string;
  name: string;
  description: string;
  fileCount: number;
  members: number;
  status: 'active' | 'completed' | 'pending';
  lastUpdated: string;
}

const projects: Project[] = [
  {
    id: '1',
    name: 'Election Deepfake Investigation',
    description: 'Analysis of viral election-related media',
    fileCount: 24,
    members: 5,
    status: 'active',
    lastUpdated: '2024-12-08',
  },
  {
    id: '2',
    name: 'Corporate Fraud Case #2847',
    description: 'Document verification for legal proceedings',
    fileCount: 156,
    members: 8,
    status: 'active',
    lastUpdated: '2024-12-07',
  },
  {
    id: '3',
    name: 'News Media Fact-Check Q4',
    description: 'Quarterly fact-checking initiative',
    fileCount: 89,
    members: 3,
    status: 'completed',
    lastUpdated: '2024-12-05',
  },
  {
    id: '4',
    name: 'Social Media Misinformation Study',
    description: 'Academic research collaboration',
    fileCount: 47,
    members: 12,
    status: 'active',
    lastUpdated: '2024-12-08',
  },
];

export function ProjectsPage({ userMode }: ProjectsPageProps) {
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  return (
    <div className="min-h-screen pt-20 pb-12 px-8">


      <div className="relative z-10 max-w-[1600px] mx-auto">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl mb-2 text-foreground">Projects</h1>
            <p className="text-muted-foreground">Organize and collaborate on investigations</p>
          </div>
          <button className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#00FFC3] to-[#99F8FF] text-black hover:shadow-[0_0_40px_rgba(0,255,195,0.4)] transition-all flex items-center gap-2">
            <Plus className="w-5 h-5" />
            <span>New Project</span>
          </button>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Projects Grid */}
          <div className="col-span-2 grid grid-cols-2 gap-4">
            {projects.map((project) => (
              <button
                key={project.id}
                onClick={() => setSelectedProject(project)}
                className={`p-6 rounded-2xl backdrop-blur-md border transition-all text-left relative overflow-hidden group ${selectedProject?.id === project.id
                  ? 'bg-white/10 border-[#00FFC3]/50'
                  : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                  }`}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="relative">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 border border-primary/30 flex items-center justify-center">
                      <FolderKanban className="w-6 h-6 text-primary" />
                    </div>
                    <div className={`px-2 py-1 rounded text-xs ${project.status === 'active'
                      ? 'bg-primary/10 text-primary border border-primary/30'
                      : project.status === 'completed'
                        ? 'bg-muted/10 text-muted-foreground border border-border/20'
                        : 'bg-secondary/10 text-secondary border border-secondary/30'
                      }`}>
                      {project.status}
                    </div>
                  </div>

                  <h3 className="text-lg mb-2 text-foreground">{project.name}</h3>
                  <p className="text-sm text-muted-foreground mb-4">{project.description}</p>

                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      <span>{project.fileCount} files</span>
                    </div>
                    {userMode === 'Professional' && (
                      <div className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        <span>{project.members} members</span>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 pt-4 border-t border-border/10 flex items-center justify-between text-xs text-muted-foreground/60">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      <span>{project.lastUpdated}</span>
                    </div>
                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Project Details Panel */}
          <div className="col-span-1">
            {selectedProject ? (
              <div className="p-6 rounded-2xl backdrop-blur-md bg-card border border-border/50 sticky top-24">
                <h3 className="text-xl mb-4 text-foreground">Project Overview</h3>

                <div className="space-y-4 mb-6">
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">Project Name</div>
                    <div className="text-sm text-foreground">{selectedProject.name}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">Status</div>
                    <div className="text-sm capitalize text-foreground">{selectedProject.status}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">Total Files</div>
                    <div className="text-sm text-foreground">{selectedProject.fileCount}</div>
                  </div>
                  {userMode === 'Professional' && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Team Members</div>
                      <div className="text-sm text-foreground">{selectedProject.members}</div>
                    </div>
                  )}
                </div>

                {/* File List */}
                <div className="mb-6">
                  <div className="text-sm text-muted-foreground mb-3">Recent Files</div>
                  <div className="space-y-2">
                    {[
                      { name: 'evidence_001.jpg', type: 'image' },
                      { name: 'witness_video.mp4', type: 'video' },
                      { name: 'article_analysis.pdf', type: 'document' },
                    ].map((file, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-lg bg-muted/20 border border-border/20 flex items-center gap-3"
                      >
                        <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center">
                          <FileText className="w-4 h-4 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs truncate text-foreground">{file.name}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Activity Timeline */}
                <div className="mb-6">
                  <div className="text-sm text-muted-foreground mb-3">Recent Activity</div>
                  <div className="space-y-3">
                    {[
                      { action: 'File uploaded', time: '2 hours ago' },
                      { action: 'Analysis completed', time: '5 hours ago' },
                      { action: 'Comment added', time: '1 day ago' },
                    ].map((activity, i) => (
                      <div key={i} className="flex items-start gap-3">
                        <div className="w-2 h-2 mt-1.5 rounded-full bg-primary" />
                        <div className="flex-1">
                          <div className="text-xs text-foreground">{activity.action}</div>
                          <div className="text-xs text-muted-foreground/60">{activity.time}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Team Members */}
                {userMode === 'Professional' && (
                  <div className="mb-6">
                    <div className="text-sm text-muted-foreground mb-3">Team</div>
                    <div className="flex -space-x-2">
                      {[...Array(selectedProject.members)].map((_, i) => (
                        <div
                          key={i}
                          className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary border-2 border-background flex items-center justify-center text-black text-xs"
                        >
                          {String.fromCharCode(65 + i)}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Comments */}
                <div>
                  <div className="text-sm text-muted-foreground mb-3">Comments</div>
                  <div className="relative">
                    <MessageSquare className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                    <textarea
                      placeholder="Add a comment..."
                      className="w-full pl-10 pr-4 py-3 rounded-lg bg-muted/20 border border-border/20 focus:border-primary/30 focus:outline-none resize-none text-sm text-foreground placeholder-muted-foreground"
                      rows={3}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6 rounded-2xl backdrop-blur-md bg-card border border-border/50 h-full flex items-center justify-center text-center sticky top-24">
                <div>
                  <FolderKanban className="w-12 h-12 text-muted-foreground/40 mx-auto mb-3" />
                  <p className="text-muted-foreground">Select a project to view details</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
