/**
 * HTML 模板简历渲染器
 * 将简历数据渲染为标准的 HTML 格式
 */
import React from 'react';
import './HTMLTemplateRenderer.css';

const HTMLTemplateRenderer = ({ resumeData }) => {
  if (!resumeData) {
    return <div className="text-gray-400">暂无简历数据</div>;
  }

  const basic = resumeData.basic || {};
  const education = resumeData.education || [];
  const experience = resumeData.experience || [];
  const projects = resumeData.projects || [];
  const openSource = resumeData.openSource || [];
  const awards = resumeData.awards || [];
  const skillContent = resumeData.skillContent || '';
  const menuSections = resumeData.menuSections || [];

  // 过滤出启用的模块
  const enabledSections = menuSections
    .filter(section => section.enabled)
    .sort((a, b) => a.order - b.order);

  // 渲染函数
  const renderSection = (sectionId) => {
    switch (sectionId) {
      case 'basic':
        return (
          <div className="template-section" key="basic">
            <h3 className="section-title">基本信息</h3>
            <div className="section-content">
              <p><strong>姓名:</strong> {basic.name || 'N/A'}</p>
              <p><strong>目标职位:</strong> {basic.title || 'N/A'}</p>
              {basic.email && <p><strong>邮箱:</strong> {basic.email}</p>}
              {basic.phone && <p><strong>电话:</strong> {basic.phone}</p>}
              {basic.location && <p><strong>地点:</strong> {basic.location}</p>}
              {basic.employementStatus && (
                <span className="employment-status">{basic.employementStatus}</span>
              )}
            </div>
          </div>
        );

      case 'skills':
        return (
          <div className="template-section" key="skills">
            <h3 className="section-title">专业技能</h3>
            <div className="section-content"
                 dangerouslySetInnerHTML={{ __html: skillContent }} />
          </div>
        );

      case 'education':
        if (!education.length) return null;
        return (
          <div className="template-section" key="education">
            <h3 className="section-title">教育经历</h3>
            <div className="section-content">
              {education.map(edu => (
                <div className="item" key={edu.id}>
                  <div className="item-header">
                    <div className="item-title-group">
                      <h4 className="item-title">{edu.school}</h4>
                      <p className="item-subtitle">{edu.degree} in {edu.major}</p>
                    </div>
                    <span className="item-date">{edu.startDate} - {edu.endDate}</span>
                  </div>
                  {edu.gpa && <p className="item-description"><strong>GPA:</strong> {edu.gpa}</p>}
                  {edu.description && (
                    <div className="item-description"
                         dangerouslySetInnerHTML={{ __html: edu.description }} />
                  )}
                </div>
              ))}
            </div>
          </div>
        );

      case 'experience':
        if (!experience.length) return null;
        return (
          <div className="template-section" key="experience">
            <h3 className="section-title">工作经历</h3>
            <div className="section-content">
              {experience.map(exp => (
                <div className="item" key={exp.id}>
                  <div className="item-header">
                    <div className="item-title-group">
                      <h4 className="item-title">{exp.company}</h4>
                      <p className="item-subtitle">{exp.position}</p>
                    </div>
                    <span className="item-date">{exp.date}</span>
                  </div>
                  {exp.details && (
                    <div className="item-description"
                         dangerouslySetInnerHTML={{ __html: exp.details }} />
                  )}
                </div>
              ))}
            </div>
          </div>
        );

      case 'projects':
        if (!projects.length) return null;
        return (
          <div className="template-section" key="projects">
            <h3 className="section-title">项目经历</h3>
            <div className="section-content">
              {projects.map(proj => (
                <div className="item" key={proj.id}>
                  <div className="item-header">
                    <div className="item-title-group">
                      <h4 className="item-title">{proj.name}</h4>
                      <p className="item-subtitle">{proj.role}</p>
                    </div>
                    <span className="item-date">{proj.date}</span>
                  </div>
                  {proj.description && (
                    <div className="item-description"
                         dangerouslySetInnerHTML={{ __html: proj.description }} />
                  )}
                  {proj.link && (
                    <a className="item-link" href={proj.link} target="_blank" rel="noopener noreferrer">
                      项目链接
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        );

      case 'openSource':
        if (!openSource.length) return null;
        return (
          <div className="template-section" key="openSource">
            <h3 className="section-title">开源经历</h3>
            <div className="section-content">
              {openSource.map((os, idx) => (
                <div className="item" key={os.id || idx}>
                  <div className="item-header">
                    <div className="item-title-group">
                      <h4 className="item-title">{os.name}</h4>
                      {os.role && <p className="item-subtitle">{os.role}</p>}
                    </div>
                  </div>
                  {os.description && (
                    <div className="item-description"
                         dangerouslySetInnerHTML={{ __html: os.description }} />
                  )}
                  {os.repo && (
                    <a className="item-link" href={os.repo} target="_blank" rel="noopener noreferrer">
                      仓库链接
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        );

      case 'awards':
        if (!awards.length) return null;
        return (
          <div className="template-section" key="awards">
            <h3 className="section-title">荣誉奖项</h3>
            <div className="section-content">
              {awards.map((award, idx) => (
                <div className="item" key={award.id || idx}>
                  <div className="item-header">
                    <h4 className="item-title">{award.title}</h4>
                    {award.issuer && <span className="item-date">{award.issuer}</span>}
                  </div>
                  {award.date && <p className="item-description">{award.date}</p>}
                </div>
              ))}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="html-template-container">
      {/* 头部 */}
      <div className="template-header">
        <div className="header-main">
          <div className="header-left">
            <h1 className="candidate-name">{basic.name || '未命名'}</h1>
            <p className="candidate-title">{basic.title || '无职位'}</p>
          </div>
          <div className="header-right">
            {basic.email && <p className="info-item">{basic.email}</p>}
            {basic.phone && <p className="info-item">{basic.phone}</p>}
            {basic.location && <p className="info-item">{basic.location}</p>}
            {basic.employementStatus && (
              <span className="employment-status">{basic.employementStatus}</span>
            )}
          </div>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="template-content">
        {enabledSections.map(section => renderSection(section.id))}
      </div>
    </div>
  );
};

export default HTMLTemplateRenderer;
